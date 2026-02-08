import { Body, Controller, Get, Post } from '@nestjs/common';
import { ApiTags } from '@nestjs/swagger';
import { UserService } from '../services/user.service';

@ApiTags('users')
@Controller('users')
export class UserController {
  constructor(private readonly userService: UserService) {}

  @Get('organizations')
  listOrganizations() {
    return this.userService.listOrganizations();
  }

  @Post('organizations')
  createOrganization(@Body() body: { name: string; type: string }) {
    return this.userService.createOrganization(body);
  }
}
