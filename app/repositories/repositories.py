from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import AdCampaign, AdPayment, Favorite, Place, Review, SearchHistory, Settings, User
from app.schemas.place import PlaceDTO
from app.services.payment_service import build_ad_payment_payload


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
    ) -> User:
        user = await self.session.scalar(select(User).where(User.telegram_id == telegram_id))
        if user is not None:
            return user

        user = User(telegram_id=telegram_id, username=username, first_name=first_name)
        self.session.add(user)
        await self.session.flush()
        self.session.add(Settings(user_id=user.id))
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_city(self, user_id: int, city: str) -> User:
        user = await self.session.get(User, user_id)
        if user is None:
            raise ValueError("User not found")
        user.city = city
        await self.session.commit()
        await self.session.refresh(user)
        return user


class PlaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_many(self, places: list[PlaceDTO]) -> list[Place]:
        persisted: list[Place] = []
        for dto in places:
            place = await self.session.scalar(
                select(Place).where(
                    Place.provider == dto.provider,
                    Place.external_id == dto.external_id,
                )
            )
            if place is None:
                place = Place(**dto.model_dump())
                self.session.add(place)
                await self.session.flush()
            else:
                for field, value in dto.model_dump().items():
                    setattr(place, field, value)
            persisted.append(place)
        await self.session.commit()
        return persisted

    async def get_by_external_id(self, external_id: str) -> Place | None:
        return await self.session.scalar(select(Place).where(Place.external_id == external_id))


class FavoriteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_by_external_id(self, user_id: int, external_id: str) -> bool:
        place = await self.session.scalar(select(Place).where(Place.external_id == external_id))
        if place is None:
            return False

        exists = await self.session.scalar(
            select(Favorite).where(Favorite.user_id == user_id, Favorite.place_id == place.id)
        )
        if exists is not None:
            return True

        self.session.add(Favorite(user_id=user_id, place_id=place.id))
        await self.session.commit()
        return True

    async def list(self, user_id: int) -> list[Favorite]:
        result = await self.session.scalars(
            select(Favorite)
            .options(selectinload(Favorite.place))
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.created_at.desc())
            .limit(20)
        )
        return list(result.all())


class HistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(
        self,
        user_id: int,
        query_type: str,
        city: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
    ) -> None:
        self.session.add(
            SearchHistory(user_id=user_id, query_type=query_type, city=city, lat=lat, lon=lon)
        )
        await self.session.commit()

    async def list(self, user_id: int) -> list[SearchHistory]:
        result = await self.session.scalars(
            select(SearchHistory)
            .where(SearchHistory.user_id == user_id)
            .order_by(SearchHistory.created_at.desc())
            .limit(10)
        )
        return list(result.all())


class ReviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_or_update(self, user_id: int, external_id: str, rating: int, text: str | None = None) -> bool:
        place = await self.session.scalar(select(Place).where(Place.external_id == external_id))
        if place is None:
            return False
        review = await self.session.scalar(
            select(Review).where(Review.user_id == user_id, Review.place_id == place.id)
        )
        if review is None:
            review = Review(user_id=user_id, place_id=place.id, rating=rating, text=text)
            self.session.add(review)
        else:
            review.rating = rating
            review.text = text
        place.rating = await self._average_rating(place.id, pending_rating=rating, pending_user_id=user_id)
        await self.session.commit()
        return True

    async def list_for_place(self, external_id: str, limit: int = 5) -> list[Review]:
        place = await self.session.scalar(select(Place).where(Place.external_id == external_id))
        if place is None:
            return []
        result = await self.session.scalars(
            select(Review).where(Review.place_id == place.id).order_by(Review.created_at.desc()).limit(limit)
        )
        return list(result.all())

    async def _average_rating(self, place_id: int, pending_rating: int, pending_user_id: int) -> float:
        result = await self.session.scalars(
            select(Review).where(Review.place_id == place_id, Review.user_id != pending_user_id)
        )
        ratings = [review.rating for review in result.all()]
        ratings.append(pending_rating)
        return round(sum(ratings) / len(ratings), 2)


class AdRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_campaign(self, user_id: int, external_id: str, tariff_code: str, priority: int, stars_paid: int, days: int) -> bool:
        from datetime import datetime, timedelta, timezone

        place = await self.session.scalar(select(Place).where(Place.external_id == external_id))
        if place is None:
            return False
        campaign = AdCampaign(
            user_id=user_id,
            place_id=place.id,
            tariff_code=tariff_code,
            priority=priority,
            stars_paid=stars_paid,
            ends_at=datetime.now(timezone.utc) + timedelta(days=days),
        )
        self.session.add(campaign)
        await self.session.commit()
        return True

    async def create_pending_payment(
        self,
        user_id: int,
        external_id: str,
        tariff_code: str,
        stars_amount: int,
        invoice_payload: str | None = None,
    ) -> AdPayment | None:
        place = await self.session.scalar(select(Place).where(Place.external_id == external_id))
        if place is None:
            return None
        payment = AdPayment(
            user_id=user_id,
            place_id=place.id,
            tariff_code=tariff_code,
            stars_amount=stars_amount,
            status="pending",
            invoice_payload=invoice_payload,
        )
        self.session.add(payment)
        await self.session.commit()
        await self.session.refresh(payment)
        if invoice_payload is None:
            payment.invoice_payload = build_ad_payment_payload(payment.id, tariff_code, external_id)
            await self.session.commit()
            await self.session.refresh(payment)
        return payment

    async def mark_payment_paid(
        self,
        payment_id: int,
        telegram_charge_id: str | None,
        provider_charge_id: str | None,
    ) -> tuple[AdPayment | None, bool]:
        payment = await self.session.get(AdPayment, payment_id)
        if payment is None:
            return None, False
        if payment.status == "paid":
            return payment, False
        if telegram_charge_id:
            duplicate = await self.session.scalar(
                select(AdPayment).where(
                    AdPayment.telegram_payment_charge_id == telegram_charge_id,
                    AdPayment.id != payment.id,
                )
            )
            if duplicate is not None:
                return duplicate, False
        payment.status = "paid"
        payment.telegram_payment_charge_id = telegram_charge_id
        payment.provider_payment_charge_id = provider_charge_id
        await self.session.commit()
        await self.session.refresh(payment)
        return payment, True

    async def mark_payment_status(self, payment_id: int, status: str) -> AdPayment | None:
        if status not in {"pending", "paid", "failed", "cancelled"}:
            raise ValueError("Unsupported payment status")
        payment = await self.session.get(AdPayment, payment_id)
        if payment is None:
            return None
        payment.status = status
        await self.session.commit()
        await self.session.refresh(payment)
        return payment

    async def create_payment(self, user_id: int, external_id: str, tariff_code: str, stars_amount: int, telegram_charge_id: str | None, provider_charge_id: str | None) -> bool:
        payment = await self.create_pending_payment(user_id, external_id, tariff_code, stars_amount)
        if payment is None:
            return False
        await self.mark_payment_paid(payment.id, telegram_charge_id, provider_charge_id)
        return True

    async def active_for(self, category: str, city: str, limit: int = 3) -> list[Place]:
        from datetime import datetime, timezone

        result = await self.session.scalars(
            select(Place)
            .join(AdCampaign, AdCampaign.place_id == Place.id)
            .where(
                Place.category == category,
                Place.city == city,
                AdCampaign.status == "active",
                AdCampaign.ends_at > datetime.now(timezone.utc),
            )
            .order_by(AdCampaign.priority.desc(), AdCampaign.created_at.desc())
            .limit(limit)
        )
        return list(result.all())
