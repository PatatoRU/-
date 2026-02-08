import { Module } from '@nestjs/common';
import { MenuModule } from './menu.module';

@Module({
  imports: [MenuModule],
})
export class AppModule {}
