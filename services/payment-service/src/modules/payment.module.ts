import { Module } from '@nestjs/common';
import { PaymentController } from '../routes/payment.controller';
import { PaymentService } from '../services/payment.service';

@Module({
  controllers: [PaymentController],
  providers: [PaymentService],
})
export class PaymentModule {}
