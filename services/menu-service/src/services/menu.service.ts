import { Injectable } from '@nestjs/common';

const categories: { id: string; name: string; description?: string }[] = [];

@Injectable()
export class MenuService {
  getCategories() {
    return categories;
  }

  createCategory(data: { name: string; description?: string }) {
    const newCategory = {
      id: `cat_${Date.now()}`,
      name: data.name,
      description: data.description,
    };
    categories.push(newCategory);
    return newCategory;
  }
}
