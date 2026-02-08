import { Injectable } from '@nestjs/common';

@Injectable()
export class NotificationService {
  send(data: { channel: string; recipient: string; message: string }) {
    return {
      id: `notif_${Date.now()}`,
      channel: data.channel,
      recipient: data.recipient,
      message: data.message,
      status: 'queued',
    };
  }
}
