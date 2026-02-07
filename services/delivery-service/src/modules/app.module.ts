import { Module } from '@nestjs/common';
import { DeliveryModule } from './delivery.module';

@Module({
  imports: [DeliveryModule],
})
export class AppModule {}
