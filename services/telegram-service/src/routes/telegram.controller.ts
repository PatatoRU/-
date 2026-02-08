import { Body, Controller, Post } from '@nestjs/common';
import { ApiTags } from '@nestjs/swagger';
import { TelegramService } from '../services/telegram.service';

@ApiTags('telegram')
@Controller('telegram')
export class TelegramController {
  constructor(private readonly telegramService: TelegramService) {}

  @Post('webhook')
  handleWebhook(@Body() payload: { updateId: number; message?: string }) {
    return this.telegramService.handleWebhook(payload);
  }
}
