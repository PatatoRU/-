import { Body, Controller, Post } from '@nestjs/common';
import { ApiTags } from '@nestjs/swagger';
import { PaymentService } from '../services/payment.service';

@ApiTags('payments')
@Controller('payments')
export class PaymentController {
  constructor(private readonly paymentService: PaymentService) {}

  @Post('intent')
  createIntent(
    @Body()
    body: { organizationId: string; amount: number; provider: 'yookassa' | 'cloudpayments' | 'stripe' },
  ) {
    return this.paymentService.createIntent(body);
  }
}
