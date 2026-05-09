/**
 * OmniSynth - Auth utilities
 */
import Cookies from 'js-cookie'

export const setTokens = (accessToken: string, refreshToken: string) => {
  Cookies.set('access_token', accessToken, { expires: 1 })
  Cookies.set('refresh_token', refreshToken, { expires: 30 })
  localStorage.setItem('access_token', accessToken)
  localStorage.setItem('refresh_token', refreshToken)
}

export const clearTokens = () => {
  Cookies.remove('access_token')
  Cookies.remove('refresh_token')
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user')
}

export const getAccessToken = () =>
  Cookies.get('access_token') || localStorage.getItem('access_token')

export const isAuthenticated = () => !!getAccessToken()

export const saveUser = (user: any) =>
  localStorage.setItem('user', JSON.stringify(user))

export const getUser = () => {
  try {
    const u = localStorage.getItem('user')
    return u ? JSON.parse(u) : null
  } catch {
    return null
  }
}
