import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* 개발 서버가 화면 구석에 띄우는 상태 표시기를 끈다.
   *
   * 시연 영상에 그 배지가 돌아가는 게 찍힌다. 심사자에게는 「만들다 만 것」으로 보인다.
   * 다만 이건 **배지만** 없애는 것이고, 경로를 처음 열 때 컴파일하느라 멈칫하는 것은
   * 개발 서버의 성질이라 그대로다. 녹화는 `next build && next start`로 한다. */
  devIndicators: false,
};

export default nextConfig;
