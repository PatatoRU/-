import { Module } from '@nestjs/common';
import { DeliveryController } from '../routes/delivery.controller';
import { DeliveryService } from '../services/delivery.service';

@Module({
  controllers: [DeliveryController],
  providers: [DeliveryService],
})
export class DeliveryModule {}
