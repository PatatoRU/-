import { Injectable } from '@nestjs/common';

@Injectable()
export class PaymentService {
  createIntent(data: { organizationId: string; amount: number; provider: string }) {
    return {
      id: `pay_${Date.now()}`,
      organizationId: data.organizationId,
      amount: data.amount,
      provider: data.provider,
      status: 'pending',
    };
  }
}
