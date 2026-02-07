import { Module } from '@nestjs/common';
import { MenuController } from '../routes/menu.controller';
import { MenuService } from '../services/menu.service';

@Module({
  controllers: [MenuController],
  providers: [MenuService],
})
export class MenuModule {}
