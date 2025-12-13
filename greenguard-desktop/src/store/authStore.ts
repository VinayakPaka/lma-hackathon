import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
    id: number
    name: string
    email: string
    role: string
}

interface AuthState {
    user: User | null
    accessToken: string | null
    refreshToken: string | null
    isAuthenticated: boolean
    login: (user: User, accessToken: string, refreshToken: string) => void
    logout: () => void
    setTokens: (accessToken: string, refreshToken: string) => void
    testLogin: () => void
}

// TEST USER - bypass auth for development
const TEST_USER: User = {
    id: 1,
    name: 'Vinay (Test)',
    email: 'vinayreddyyedula@gmail.com',
    role: 'admin'
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            // AUTO-LOGIN FOR TESTING - bypass auth
            user: TEST_USER,
            accessToken: 'test-token-bypass',
            refreshToken: 'test-refresh-bypass',
            isAuthenticated: true, // Set to true to bypass login

            login: (user, accessToken, refreshToken) =>
                set({
                    user,
                    accessToken,
                    refreshToken,
                    isAuthenticated: true,
                }),
            logout: () =>
                set({
                    user: null,
                    accessToken: null,
                    refreshToken: null,
                    isAuthenticated: false,
                }),
            setTokens: (accessToken, refreshToken) =>
                set({ accessToken, refreshToken }),
            testLogin: () =>
                set({
                    user: TEST_USER,
                    accessToken: 'test-token-bypass',
                    refreshToken: 'test-refresh-bypass',
                    isAuthenticated: true,
                }),
        }),
        {
            name: 'greenguard-auth',
        }
    )
)
