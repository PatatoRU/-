import { Module } from '@nestjs/common';
import { UserController } from '../routes/user.controller';
import { UserService } from '../services/user.service';

@Module({
  controllers: [UserController],
  providers: [UserService],
})
export class UserModule {}
