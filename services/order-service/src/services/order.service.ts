import { Injectable } from '@nestjs/common';

const orders: {
  id: string;
  organizationId: string;
  type: 'delivery' | 'pickup' | 'dine_in';
  items: { dishId: string; quantity: number }[];
  status: string;
}[] = [];

@Injectable()
export class OrderService {
  list() {
    return orders;
  }

  create(data: {
    organizationId: string;
    type: 'delivery' | 'pickup' | 'dine_in';
    items: { dishId: string; quantity: number }[];
  }) {
    const newOrder = {
      id: `order_${Date.now()}`,
      organizationId: data.organizationId,
      type: data.type,
      items: data.items,
      status: 'new',
    };
    orders.push(newOrder);
    return newOrder;
  }

  updateStatus(id: string, status: string) {
    const order = orders.find((item) => item.id === id);
    if (!order) {
      return { error: 'not_found' };
    }
    order.status = status;
    return order;
  }
}
