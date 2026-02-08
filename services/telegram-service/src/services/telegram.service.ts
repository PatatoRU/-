import { Injectable } from '@nestjs/common';

@Injectable()
export class TelegramService {
  handleWebhook(payload: { updateId: number; message?: string }) {
    return { status: 'received', updateId: payload.updateId };
  }
}
