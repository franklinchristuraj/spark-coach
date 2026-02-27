import { NextRequest, NextResponse } from "next/server"

const PUBLIC_PATHS = ["/login"]

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Allow public paths through
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next()
  }

  // Check for JWT cookie
  const token = request.cookies.get("spark_token")?.value

  if (!token) {
    const loginUrl = new URL("/login", request.url)
    loginUrl.searchParams.set("from", pathname)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  // Run on all routes except static files and Next.js internals
  matcher: ["/((?!_next/static|_next/image|favicon.ico|icon.*|apple-icon.*).*)"],
}
