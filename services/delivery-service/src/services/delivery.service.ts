import { Injectable } from '@nestjs/common';

const zones: { id: string; name: string; minOrder: number; fee: number }[] = [];

@Injectable()
export class DeliveryService {
  listZones() {
    return zones;
  }

  createZone(data: { name: string; minOrder: number; fee: number }) {
    const zone = {
      id: `zone_${Date.now()}`,
      name: data.name,
      minOrder: data.minOrder,
      fee: data.fee,
    };
    zones.push(zone);
    return zone;
  }
}
