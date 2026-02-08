import { Body, Controller, Post } from '@nestjs/common';
import { ApiTags } from '@nestjs/swagger';
import { NotificationService } from '../services/notification.service';

@ApiTags('notifications')
@Controller('notifications')
export class NotificationController {
  constructor(private readonly notificationService: NotificationService) {}

  @Post('send')
  send(
    @Body()
    body: { channel: 'email' | 'sms' | 'telegram'; recipient: string; message: string },
  ) {
    return this.notificationService.send(body);
  }
}
