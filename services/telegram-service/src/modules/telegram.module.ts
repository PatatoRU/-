import { Module } from '@nestjs/common';
import { TelegramController } from '../routes/telegram.controller';
import { TelegramService } from '../services/telegram.service';

@Module({
  controllers: [TelegramController],
  providers: [TelegramService],
})
export class TelegramModule {}
