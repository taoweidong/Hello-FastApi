import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

// Mock heavy dependencies before importing app
const mockReplace = vi.fn();
const mockPush = vi.fn();
const mockHistory = {
  location: {
    pathname: '/welcome',
    search: '',
    hash: '',
  },
  replace: mockReplace,
  push: mockPush,
};

const mockGetMine = vi.fn();
const mockGetAsyncRoutes = vi.fn();

vi.mock('@umijs/max', () => ({
  history: mockHistory,
  Link: ({ children }: { children?: React.ReactNode }) => children,
  getAllLocales: vi.fn(() => ['zh-CN', 'en-US']),
  getLocale: vi.fn(() => 'zh-CN'),
  setLocale: vi.fn(),
}));

vi.mock('@/services/api', () => ({
  getMine: mockGetMine,
  getAsyncRoutes: mockGetAsyncRoutes,
  logout: vi.fn(),
  getLatestNotices: vi.fn(async () => []),
}));

vi.mock('../config/defaultSettings', () => ({
  default: { title: 'PureAdmin React' },
}));

// WebSocket 实时通道与 getInitialState 无关，测试中隔离掉真实连接
vi.mock('./utils/websocket', () => ({
  realtime: {
    start: vi.fn(),
    stop: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
  },
}));

describe('app getInitialState', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.unstubAllGlobals();
    mockHistory.location = {
      pathname: '/welcome',
      search: '',
      hash: '',
    };
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('should fetch mine info and async routes when not on login page', async () => {
    const { getInitialState } = await import('./app');
    const mine = {
      username: 'admin',
      nickname: '管理员',
      avatar: '',
      email: '',
      phone: '',
    };
    mockGetMine.mockResolvedValue(mine);
    mockGetAsyncRoutes.mockResolvedValue([]);

    const state = await getInitialState();

    expect(mockGetMine).toHaveBeenCalled();
    expect(mockGetAsyncRoutes).toHaveBeenCalled();
    expect(state.currentUser).toEqual(mine);
    expect(state.menus).toEqual([]);
    expect(state.fetchUserInfo).toBeDefined();
  });

  it('should read permission codes stored at login', async () => {
    const { getInitialState } = await import('./app');
    mockGetMine.mockResolvedValue({
      username: 'admin',
      nickname: '',
      avatar: '',
      email: '',
      phone: '',
    });
    mockGetAsyncRoutes.mockResolvedValue([]);
    // node 测试环境无 localStorage，使用 stub 模拟登录时写入的权限码
    vi.stubGlobal('localStorage', {
      getItem: (key: string) =>
        key === 'react-admin-auth'
          ? JSON.stringify({
              state: { permissions: ['user:add', 'user:edit'] },
            })
          : null,
    });

    const state = await getInitialState();

    expect(state.permissions).toEqual(['user:add', 'user:edit']);
  });

  it('should redirect to login when mine fetch fails', async () => {
    const { getInitialState } = await import('./app');
    mockGetMine.mockRejectedValue(new Error('401 Unauthorized'));
    mockGetAsyncRoutes.mockResolvedValue([]);

    const state = await getInitialState();

    expect(mockReplace).toHaveBeenCalledWith('/user/login');
    expect(state.currentUser).toBeUndefined();
  });

  it('should not fetch mine info on login page', async () => {
    const { getInitialState } = await import('./app');
    mockHistory.location = {
      pathname: '/user/login',
      search: '',
      hash: '',
    };

    const state = await getInitialState();

    expect(mockGetMine).not.toHaveBeenCalled();
    expect(mockGetAsyncRoutes).not.toHaveBeenCalled();
    expect(state.currentUser).toBeUndefined();
    expect(state.fetchUserInfo).toBeDefined();
  });

  it('should include default settings in initial state', async () => {
    const { getInitialState } = await import('./app');
    mockGetMine.mockResolvedValue({
      username: 'admin',
      nickname: '',
      avatar: '',
      email: '',
      phone: '',
    });
    mockGetAsyncRoutes.mockResolvedValue([]);

    const state = await getInitialState();

    expect(state.settings).toEqual({ title: 'PureAdmin React' });
  });

  it('fetchUserInfo should return user data on success', async () => {
    const { getInitialState } = await import('./app');
    const mine = {
      username: 'admin',
      nickname: 'Fetched',
      avatar: '',
      email: '',
      phone: '',
    };
    mockGetMine.mockResolvedValue(mine);
    mockGetAsyncRoutes.mockResolvedValue([]);

    const state = await getInitialState();

    const user = await state.fetchUserInfo?.();
    expect(user).toEqual(mine);
  });
});
