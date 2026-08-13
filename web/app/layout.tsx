import type { Metadata } from "next";
import { Suspense } from "react";
import Shell from "@/components/Shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "정책핏 인천",
  description:
    "인천 6대 전략산업의 사업과 산업 수요를 대조해, 어긋난 곳을 후보로 골라냅니다. 확정은 부서 협의로 합니다.",
};

export const dynamic = "force-dynamic";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <head>
        {/*
          활자 셋: 제목은 송명체(문서의 얼굴), 본문은 IBM Plex Sans KR(읽는 글),
          숫자와 신호 번호는 IBM Plex Mono(원장의 값). 셋의 역할을 섞지 않는다.

          next/font를 쓰지 않고 링크로 받는다 — next/font의 폰트 목록에는 이 두 한글 서체의
          korean 서브셋이 없어서, 그대로 쓰면 한글이 시스템 글꼴로 떨어진다.
          이 화면이 바깥으로 나가는 요청은 이 한 줄뿐이다.
        */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Song+Myung&family=IBM+Plex+Sans+KR:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap"
        />
      </head>
      <body>
        <Suspense>
          <Shell>{children}</Shell>
        </Suspense>
      </body>
    </html>
  );
}
