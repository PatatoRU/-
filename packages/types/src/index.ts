export type OrganizationId = string;

export interface Category {
  id: string;
  organizationId: OrganizationId;
  name: string;
  description?: string;
  sortOrder: number;
  parentId?: string | null;
  isActive: boolean;
}

export interface ModifierOption {
  label: string;
  priceDelta: number;
}

export interface ModifierGroup {
  id: string;
  name: string;
  options: ModifierOption[];
}

export interface Dish {
  id: string;
  categoryId: string;
  name: string;
  description?: string;
  price: number;
  imageUrl?: string;
  cookingTimeMin?: number;
  isAvailable: boolean;
  modifiers: ModifierGroup[];
}

export interface OrderItem {
  dishId: string;
  quantity: number;
  modifiers: { groupId: string; optionLabel: string }[];
  comment?: string;
}

export interface Order {
  id: string;
  organizationId: OrganizationId;
  type: 'delivery' | 'pickup' | 'dine_in';
  status: 'new' | 'accepted' | 'cooking' | 'ready' | 'delivering' | 'completed' | 'cancelled';
  items: OrderItem[];
  total: number;
  createdAt: string;
}
