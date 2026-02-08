import { Body, Controller, Get, Post } from '@nestjs/common';
import { ApiTags } from '@nestjs/swagger';
import { DeliveryService } from '../services/delivery.service';

@ApiTags('delivery')
@Controller('delivery')
export class DeliveryController {
  constructor(private readonly deliveryService: DeliveryService) {}

  @Get('zones')
  listZones() {
    return this.deliveryService.listZones();
  }

  @Post('zones')
  createZone(
    @Body()
    body: { name: string; minOrder: number; fee: number },
  ) {
    return this.deliveryService.createZone(body);
  }
}
