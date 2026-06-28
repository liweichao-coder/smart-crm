import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { AUTH_STORAGE_KEY, fetchCurrentUser, login as loginApi, logout as logoutApi } from '../api.js'

const AuthContext = createContext(null)

function readStoredSession() {
  try {
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function writeStoredSession(session) {
  if (session) {
    window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session))
  } else {
    window.localStorage.removeItem(AUTH_STORAGE_KEY)
  }
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => readStoredSession())
  const [loading, setLoading] = useState(Boolean(readStoredSession()?.token))

  // 用持久化 token 复核当前用户，token 失效则清理。
  useEffect(() => {
    let active = true
    const token = session?.token
    if (!token) {
      setLoading(false)
      return undefined
    }
    fetchCurrentUser()
      .then((data) => {
        if (!active) return
        setSession((prev) => ({ ...prev, ...data, token }))
      })
      .catch(() => {
        if (!active) return
        writeStoredSession(null)
        setSession(null)
      })
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
    // 仅在初次挂载时复核
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const login = useCallback(async (account, password) => {
    const data = await loginApi({ account, password })
    writeStoredSession(data)
    setSession(data)
    return data
  }, [])

  const logout = useCallback(async () => {
    try {
      await logoutApi()
    } catch {
      // 即使后端登出失败也清理本地会话
    }
    writeStoredSession(null)
    setSession(null)
  }, [])

  const value = useMemo(
    () => ({
      session,
      user: session?.user ?? null,
      organizations: session?.organizations ?? [],
      permissions: session?.user?.permissions ?? [],
      isAuthenticated: Boolean(session?.token),
      loading,
      login,
      logout,
    }),
    [session, loading, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}

export function hasPermission(permissions, required) {
  if (!required) return true
  if (!permissions) return false
  return permissions.includes('*') || permissions.includes(required)
}
