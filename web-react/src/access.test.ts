import { describe, expect, it } from 'vitest';
import access from './access';

describe('access', () => {
  it('should return hasPermission true when user has the permission code', () => {
    const result = access({ permissions: ['user:add', 'user:edit'] });

    expect(result.hasPermission('user:add')).toBe(true);
    expect(result.hasPermission('user:edit')).toBe(true);
  });

  it('should return hasPermission false for unknown permission codes', () => {
    const result = access({ permissions: ['user:add'] });

    expect(result.hasPermission('role:add')).toBe(false);
  });

  it('should return hasPermission false when permissions is undefined', () => {
    const result = access({ permissions: undefined });

    expect(result.hasPermission('user:add')).toBe(false);
  });

  it('should return hasPermission false when initialState is undefined', () => {
    const result = access(undefined);

    expect(result.hasPermission('user:add')).toBe(false);
  });

  it('should return isAdmin true only for the admin user', () => {
    expect(access({ currentUser: { username: 'admin' } }).isAdmin).toBe(true);
    expect(access({ currentUser: { username: 'alice' } }).isAdmin).toBe(false);
  });

  it('should return isAdmin false when currentUser is undefined', () => {
    expect(access({ currentUser: undefined }).isAdmin).toBe(false);
    expect(access(undefined).isAdmin).toBe(false);
  });
});
