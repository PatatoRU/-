import { Injectable } from '@nestjs/common';

const organizations: { id: string; name: string; type: string }[] = [];

@Injectable()
export class UserService {
  listOrganizations() {
    return organizations;
  }

  createOrganization(data: { name: string; type: string }) {
    const org = {
      id: `org_${Date.now()}`,
      name: data.name,
      type: data.type,
    };
    organizations.push(org);
    return org;
  }
}
