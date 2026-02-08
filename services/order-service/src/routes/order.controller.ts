import { Body, Controller, Get, Param, Patch, Post } from '@nestjs/common';
import { ApiTags } from '@nestjs/swagger';
import { OrderService } from '../services/order.service';

@ApiTags('orders')
@Controller('orders')
export class OrderController {
  constructor(private readonly orderService: OrderService) {}

  @Get()
  list() {
    return this.orderService.list();
  }

  @Post()
  create(
    @Body()
    body: {
      organizationId: string;
      type: 'delivery' | 'pickup' | 'dine_in';
      items: { dishId: string; quantity: number }[];
    },
  ) {
    return this.orderService.create(body);
  }

  @Patch(':id/status')
  updateStatus(@Param('id') id: string, @Body() body: { status: string }) {
    return this.orderService.updateStatus(id, body.status);
  }
}
