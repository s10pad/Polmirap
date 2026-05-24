'use client'

import { useEffect, useRef } from 'react'
import { DottedSurface } from '@/components/ui/dotted-surface'
import { cn } from '@/lib/utils'

/* ─── tiny helpers ─────────────────────────────────────── */

/** Pentagon-prism crystal */
function Prism({
  w = 168,
  h = 232,
  holoGradient,
  spinDur = '9s',
  className,
}: {
  w?: number
  h?: number
  holoGradient?: string
  spinDur?: string
  className?: string
}) {
  const grad =
    holoGradient ??
    'conic-gradient(from 0deg at 50% 50%,transparent 0deg,rgba(255,45,85,.9) 12deg,rgba(255,107,0,.7) 32deg,rgba(255,214,10,.6) 52deg,rgba(0,230,118,.75) 72deg,rgba(0,229,255,.9) 92deg,rgba(68,138,255,.7) 112deg,rgba(234,128,252,.8) 132deg,transparent 155deg,transparent 360deg)'

  return (
    <div style={{ width: w, height: h, position: 'relative' }}>
      {/* body */}
      <div
        className="clip-prism absolute inset-0 overflow-hidden"
        style={{ background: '#03070d' }}
      >
        {/* holo layer */}
        <div
          className="holo-layer"
          style={{ background: grad, animationDuration: spinDur }}
        />
        {/* dark radial overlay for depth */}
        <div
          className="absolute inset-0"
          style={{
            background:
              'radial-gradient(ellipse at 38% 35%,transparent 28%,rgba(0,0,0,.55) 100%)',
          }}
        />
      </div>
      {/* edge highlight */}
      <div
        className="clip-prism pointer-events-none absolute inset-0"
        style={{
          boxShadow:
            'inset 0 0 24px rgba(0,229,255,.06),0 0 60px rgba(100,0,220,.18),0 0 120px rgba(0,229,255,.08)',
        }}
      />
    </div>
  )
}

/** Diamond crystal */
function Diamond({
  size = 30,
  holoGradient,
  spinDur = '6s',
  floatDur = '6s',
  floatDelay = '0s',
  className,
  style,
}: {
  size?: number
  holoGradient?: string
  spinDur?: string
  floatDur?: string
  floatDelay?: string
  className?: string
  style?: React.CSSProperties
}) {
  const grad =
    holoGradient ??
    'conic-gradient(from 0deg,rgba(255,45,85,.9),rgba(234,128,252,.8),rgba(0,229,255,.9),rgba(255,45,85,.9))'

  return (
    <div
      className={cn('absolute', className)}
      style={{
        animation: `float-y ${floatDur} ease-in-out infinite`,
        animationDelay: floatDelay,
        ...style,
      }}
    >
      <div style={{ width: size, height: size, position: 'relative' }}>
        <div
          className="clip-diamond absolute inset-0 overflow-hidden"
          style={{ background: '#03070d' }}
        >
          <div
            className="holo-layer-sm"
            style={{ background: grad, animationDuration: spinDur }}
          />
        </div>
      </div>
    </div>
  )
}

/** Section label with leading rule */
function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="mb-5 flex items-center gap-3 font-mono text-[0.62rem] uppercase tracking-[0.2em]"
      style={{ color: 'rgba(255,255,255,0.42)' }}
    >
      <span className="inline-block h-px w-5" style={{ background: 'rgba(255,255,255,0.42)' }} />
      {children}
    </div>
  )
}

/** Spectrum divider */
function SpecRule() {
  return <div className="spec-rule" />
}

/* ─── main page ────────────────────────────────────────── */

export default function Home() {
  /* scroll-reveal */
  const revealRefs = useRef<HTMLDivElement[]>([])
  useEffect(() => {
    const io = new IntersectionObserver(
      (entries) => entries.forEach((e) => { if (e.isIntersecting) e.target.classList.add('in') }),
      { threshold: 0.1 },
    )
    revealRefs.current.forEach((el) => el && io.observe(el))
    return () => io.disconnect()
  }, [])

  /* nav sticky */
  const navRef = useRef<HTMLElement>(null)
  useEffect(() => {
    const onScroll = () => navRef.current?.classList.toggle('sticky-nav', window.scrollY > 50)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const addReveal = (el: HTMLDivElement | null) => {
    if (el && !revealRefs.current.includes(el)) revealRefs.current.push(el)
  }

  /* ── render ── */
  return (
    <>
      {/* ── Three.js dotted background ── */}
      <DottedSurface />

      {/* ── NAV ── */}
      <nav
        ref={navRef}
        className="fixed left-0 right-0 top-0 z-50 flex items-center justify-between px-14 py-7 transition-all duration-300"
        style={{ ['--sticky-bg' as string]: 'rgba(0,0,0,0.85)' }}
      >
        <style>{`
          .sticky-nav {
            background: rgba(0,0,0,0.85);
            backdrop-filter: blur(28px) saturate(180%);
            border-bottom: 1px solid rgba(255,255,255,0.07);
          }
        `}</style>
        <a
          href="#"
          className="font-syncopate text-[0.78rem] font-bold uppercase tracking-[0.2em] text-white no-underline"
        >
          MIRROR AI
        </a>
        <ul className="hidden items-center gap-10 list-none md:flex">
          {['Feed', 'Positions', 'Roster', 'Docs'].map((l) => (
            <li key={l}>
              <a
                href={`#${l.toLowerCase()}`}
                className="text-[0.72rem] uppercase tracking-[0.1em] no-underline transition-colors"
                style={{ color: 'rgba(255,255,255,0.42)' }}
                onMouseEnter={(e) => (e.currentTarget.style.color = '#fff')}
                onMouseLeave={(e) => (e.currentTarget.style.color = 'rgba(255,255,255,0.42)')}
              >
                {l}
              </a>
            </li>
          ))}
        </ul>
        <a
          href="#"
          className="bg-white px-6 py-2.5 font-barlow text-[0.7rem] font-semibold uppercase tracking-[0.12em] text-black no-underline transition-opacity hover:opacity-90"
        >
          Launch App
        </a>
      </nav>

      {/* ── HERO ── */}
      <section className="relative flex min-h-screen flex-col items-center overflow-hidden px-8 pb-20 pt-28 text-center">
        {/* ambient radial glow */}
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              'radial-gradient(ellipse 65% 55% at 50% 18%,rgba(90,0,200,.13) 0%,transparent 70%),radial-gradient(ellipse 40% 35% at 15% 85%,rgba(0,180,100,.05) 0%,transparent 60%),radial-gradient(ellipse 40% 35% at 85% 75%,rgba(0,80,255,.06) 0%,transparent 60%)',
          }}
        />

        {/* live badge */}
        <div
          className="mb-11 inline-flex items-center gap-2.5 border px-4 py-1.5 font-mono text-[0.62rem] uppercase tracking-[0.18em]"
          style={{
            color: 'rgba(255,255,255,0.42)',
            borderColor: 'rgba(255,255,255,0.14)',
            opacity: 0,
            animation: 'fade-up 0.6s ease 0.2s forwards',
          }}
        >
          <span
            className="inline-block h-1.5 w-1.5 rounded-full bg-[#00e676]"
            style={{ animation: 'blink 2.2s ease-in-out infinite' }}
          />
          Live — Paper trading enabled
        </div>

        {/* wordmark */}
        <h1
          className="mb-6 font-syncopate text-[clamp(2.8rem,8.5vw,6.8rem)] font-bold uppercase leading-none tracking-[0.08em]"
          style={{ opacity: 0, animation: 'fade-up 0.8s ease 0.38s forwards' }}
        >
          MIRROR AI
        </h1>

        {/* subtitle */}
        <p
          className="mb-14 text-[clamp(.82rem,1.6vw,.96rem)] font-light uppercase tracking-[0.12em]"
          style={{
            color: 'rgba(255,255,255,0.42)',
            opacity: 0,
            animation: 'fade-up 0.7s ease 0.54s forwards',
          }}
        >
          Mirror the trades of those who know
        </p>

        {/* ── Crystal stage ── */}
        <div
          className="relative mx-auto mb-8 w-full max-w-[900px]"
          style={{
            height: 460,
            opacity: 0,
            animation: 'fade-up 1.1s ease 0.28s forwards',
          }}
        >
          {/* ambient glow */}
          <div
            className="pointer-events-none absolute"
            style={{
              top: '50%', left: '50%',
              width: 340, height: 460,
              transform: 'translate(-50%,-50%)',
              background: 'radial-gradient(ellipse,rgba(110,0,240,.22) 0%,rgba(0,229,255,.1) 38%,transparent 68%)',
              filter: 'blur(38px)',
              animation: 'glow-pulse 4.5s ease-in-out infinite',
            }}
          />

          {/* Light rays SVG */}
          <svg
            className="pointer-events-none absolute inset-0 h-full w-full"
            viewBox="0 0 900 460"
            preserveAspectRatio="none"
          >
            <defs>
              {[
                ['gr', '#ff2d55'],
                ['gg', '#00e676'],
                ['gc', '#00e5ff'],
                ['gp', '#ea80fc'],
              ].map(([id, color]) => (
                <linearGradient key={id} id={id} x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor={color} stopOpacity="0.75" />
                  <stop offset="100%" stopColor={color} stopOpacity="0" />
                </linearGradient>
              ))}
              {[
                ['grl', '#ff2d55', 0.45],
                ['gcl', '#00e5ff', 0.35],
              ].map(([id, color, op]) => (
                <linearGradient key={id as string} id={id as string} x1="1" y1="0" x2="0" y2="0">
                  <stop offset="0%" stopColor={color as string} stopOpacity={op as number} />
                  <stop offset="100%" stopColor={color as string} stopOpacity="0" />
                </linearGradient>
              ))}
            </defs>
            {/* right rays */}
            <line x1="455" y1="226" x2="900" y2="195" stroke="url(#gr)" strokeWidth="1.4" style={{ animation: 'ray-fade 3.2s ease-in-out infinite' }} />
            <line x1="455" y1="236" x2="900" y2="258" stroke="url(#gg)" strokeWidth="1.4" style={{ animation: 'ray-fade 3.2s ease-in-out 0.55s infinite' }} />
            <line x1="455" y1="246" x2="900" y2="316" stroke="url(#gc)" strokeWidth="1.4" style={{ animation: 'ray-fade 3.2s ease-in-out 1.1s infinite' }} />
            <line x1="455" y1="232" x2="900" y2="178" stroke="url(#gp)" strokeWidth="1"   style={{ animation: 'ray-fade 3.2s ease-in-out 1.7s infinite' }} />
            {/* left rays */}
            <line x1="445" y1="226" x2="0"   y2="195" stroke="url(#grl)" strokeWidth="1"   style={{ animation: 'ray-fade 3.2s ease-in-out 0.3s infinite' }} />
            <line x1="445" y1="244" x2="0"   y2="310" stroke="url(#gcl)" strokeWidth="1"   style={{ animation: 'ray-fade 3.2s ease-in-out 0.9s infinite' }} />
          </svg>

          {/* main prism */}
          <div
            className="absolute"
            style={{
              top: '50%', left: '50%',
              transform: 'translate(-50%,-50%)',
              animation: 'float-y 8s ease-in-out infinite',
            }}
          >
            <Prism w={168} h={232} />
          </div>

          {/* floating mini diamonds */}
          {[
            { size: 36, top: '14%', left: '10%',  fd: '5.5s', fdd: '0s',    grad: 'conic-gradient(from 0deg,rgba(255,45,85,.9),rgba(234,128,252,.8),rgba(0,229,255,.9),rgba(255,45,85,.9))' },
            { size: 16, top:  '8%', left: '22%',  fd:   '7s', fdd: '-3s',   grad: 'conic-gradient(from 0deg,rgba(0,229,255,.9),rgba(234,128,252,.7),rgba(0,229,255,.9))' },
            { size: 24, top: '10%', right: '18%', fd: '6.5s', fdd: '-2s',   grad: 'conic-gradient(from 0deg,rgba(0,230,118,.9),rgba(0,229,255,.8),rgba(234,128,252,.7),rgba(0,230,118,.9))' },
            { size: 32, top: '24%', right:  '8%', fd: '4.8s', fdd: '-1s',   grad: 'conic-gradient(from 0deg,rgba(234,128,252,.9),rgba(68,138,255,.8),rgba(0,229,255,.9),rgba(234,128,252,.9))' },
            { size: 20, top: '55%', left:   '7%', fd: '7.5s', fdd: '-4s',   grad: 'conic-gradient(from 0deg,rgba(68,138,255,.9),rgba(0,229,255,.8),rgba(234,128,252,.7),rgba(68,138,255,.9))' },
            { size: 18, bottom: '12%', left: '25%', fd: '6s', fdd: '-5s',   grad: 'conic-gradient(from 0deg,rgba(255,45,85,.9),rgba(255,107,0,.8),rgba(255,45,85,.9))' },
            { size: 28, bottom:  '8%', right: '22%', fd: '5s', fdd: '-2.5s',grad: 'conic-gradient(from 0deg,rgba(0,229,255,.9),rgba(0,230,118,.8),rgba(68,138,255,.7),rgba(0,229,255,.9))' },
            { size: 14, bottom: '18%', right: '8%',  fd: '8s', fdd: '-1.5s',grad: 'conic-gradient(from 0deg,rgba(234,128,252,.9),rgba(255,45,85,.8),rgba(234,128,252,.9))' },
          ].map((d, i) => (
            <Diamond
              key={i}
              size={d.size}
              holoGradient={d.grad}
              floatDur={d.fd}
              floatDelay={d.fdd}
              className={cn(
                d.top    && `top-[${d.top}]`,
                (d as any).bottom && `bottom-[${(d as any).bottom}]`,
                d.left   && `left-[${d.left}]`,
                (d as any).right  && `right-[${(d as any).right}]`,
              )}
              style={{
                top:    (d as any).top,
                bottom: (d as any).bottom,
                left:   (d as any).left,
                right:  (d as any).right,
              } as React.CSSProperties}
            />
          ))}
        </div>

        {/* CTA buttons */}
        <div
          className="relative z-10 flex flex-wrap items-center justify-center gap-4"
          style={{ opacity: 0, animation: 'fade-up 0.6s ease 0.85s forwards' }}
        >
          <a href="#" className="bg-white px-8 py-3 font-barlow text-[0.72rem] font-semibold uppercase tracking-[0.12em] text-black transition-opacity hover:opacity-88">
            Get Started
          </a>
          <a
            href="#"
            className="px-8 py-3 font-barlow text-[0.72rem] font-medium uppercase tracking-[0.12em] transition-colors"
            style={{ color: 'rgba(255,255,255,0.42)', border: '1px solid rgba(255,255,255,0.14)' }}
            onMouseEnter={(e) => { e.currentTarget.style.color = '#fff'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.28)' }}
            onMouseLeave={(e) => { e.currentTarget.style.color = 'rgba(255,255,255,0.42)'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.14)' }}
          >
            View Signals
          </a>
        </div>
      </section>

      <SpecRule />

      {/* ── ABOUT ── */}
      <section id="feed" className="border-b py-32" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
        <div className="mx-auto max-w-[1160px] px-14">
          <div className="grid grid-cols-1 items-center gap-24 md:grid-cols-2">
            <div ref={addReveal} className="reveal">
              <SectionLabel>What is Mirror AI</SectionLabel>
              <h2 className="mb-6 font-barlow-condensed text-[clamp(2.1rem,4.5vw,3.9rem)] font-light leading-[1.04]">
                Your on-chain<br />edge in the market
              </h2>
              <p className="mb-10 text-[0.92rem] font-light leading-[1.8]" style={{ color: 'rgba(255,255,255,0.42)', maxWidth: 450 }}>
                A protocol that monitors public trade disclosures from politicians, executives, and high-profile investors — scoring, ranking, and automatically surfacing actionable signals for you to mirror.
              </p>
              <div className="flex flex-wrap gap-4">
                <a href="#" className="bg-white px-7 py-2.5 font-barlow text-[0.72rem] font-semibold uppercase tracking-[0.12em] text-black no-underline hover:opacity-90">View Signals</a>
                <a href="#" className="px-7 py-2.5 font-barlow text-[0.72rem] font-medium uppercase tracking-[0.12em] no-underline transition-colors" style={{ color: 'rgba(255,255,255,0.42)', border: '1px solid rgba(255,255,255,0.14)' }}>How It Works</a>
              </div>
            </div>
            <div ref={addReveal} className="reveal d2 relative flex h-[340px] items-center justify-center">
              {/* med glow */}
              <div className="pointer-events-none absolute" style={{ top: '50%', left: '50%', width: 220, height: 300, transform: 'translate(-50%,-50%)', background: 'radial-gradient(ellipse,rgba(0,229,255,.16),rgba(110,0,240,.1),transparent 68%)', filter: 'blur(28px)', animation: 'glow-pulse 4s ease-in-out infinite' }} />
              <div style={{ animation: 'float-y 7s ease-in-out infinite' }}>
                <Prism
                  w={112} h={152}
                  holoGradient="conic-gradient(from 0deg at 50% 50%,transparent,rgba(0,229,255,.9) 20deg,rgba(234,128,252,.75) 50deg,rgba(255,45,85,.85) 80deg,transparent 110deg,transparent 360deg)"
                  spinDur="6.5s"
                />
              </div>
              {[
                { size: 18, top: '8%',   left: '12%',  fd: '4.5s', fdd: '0s',  grad: 'conic-gradient(from 0deg,rgba(255,45,85,.9),rgba(234,128,252,.8),rgba(255,45,85,.9))' },
                { size: 13, top: '18%',  right: '8%',  fd: '5.5s', fdd: '-2s', grad: 'conic-gradient(from 0deg,rgba(0,229,255,.9),rgba(68,138,255,.8),rgba(0,229,255,.9))' },
                { size: 22, bottom: '12%', right: '16%', fd: '6s', fdd: '-1s', grad: 'conic-gradient(from 0deg,rgba(0,230,118,.9),rgba(0,229,255,.8),rgba(0,230,118,.9))' },
              ].map((d, i) => (
                <Diamond key={i} size={d.size} holoGradient={d.grad} floatDur={d.fd} floatDelay={d.fdd}
                  style={{ top: (d as any).top, bottom: (d as any).bottom, left: (d as any).left, right: (d as any).right } as React.CSSProperties}
                />
              ))}
            </div>
          </div>
        </div>
      </section>

      <SpecRule />

      {/* ── COUNTER ── */}
      <section className="border-b py-24 text-center" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
        <div className="mx-auto max-w-[1160px] px-14">
          <div ref={addReveal} className="reveal">
            <div
              className="font-barlow-condensed leading-none tracking-[-0.05em]"
              style={{
                fontSize: 'clamp(5.5rem,16vw,11.5rem)',
                fontWeight: 200,
                background: 'linear-gradient(140deg,#fff 35%,rgba(255,255,255,.35))',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}
            >
              100
            </div>
            <div className="mt-1 font-mono text-[0.62rem] uppercase tracking-[0.25em]" style={{ color: 'rgba(255,255,255,0.42)' }}>
              Tracked Investors Network
            </div>
            <p className="mx-auto mt-7 font-barlow-condensed font-light leading-[1.3]" style={{ fontSize: 'clamp(1.15rem,2.5vw,1.85rem)', color: 'rgba(255,255,255,0.42)', maxWidth: 580 }}>
              A real-time signal network built on public disclosures<br />
              from politicians, executives, and market movers
            </p>
          </div>
        </div>
      </section>

      <SpecRule />

      {/* ── NETWORK ── */}
      <section id="positions" className="border-b py-28 text-center" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
        <div className="mx-auto max-w-[1160px] px-14">
          <div ref={addReveal} className="reveal">
            <SectionLabel><span className="mx-auto">Signal Network</span></SectionLabel>
            <h2 className="mx-auto mb-3 font-barlow-condensed text-[clamp(2.1rem,4.5vw,3.9rem)] font-light leading-[1.04]" style={{ maxWidth: 560 }}>
              A global signal network<br />powered by public data
            </h2>
            <p className="mx-auto text-[0.88rem] font-light leading-[1.8]" style={{ color: 'rgba(255,255,255,0.42)', maxWidth: 460 }}>
              Each node is a tracked insider. When a trade disclosure is filed, the signal propagates instantly to your feed.
            </p>
          </div>

          {/* Node network */}
          <div ref={addReveal} className="reveal d1 relative mx-auto mt-16" style={{ height: 320, maxWidth: 820 }}>
            <svg className="absolute inset-0 h-full w-full" viewBox="0 0 820 320">
              <defs>
                <linearGradient id="nl" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%"   stopColor="rgba(0,229,255,0)" />
                  <stop offset="50%"  stopColor="rgba(0,229,255,.22)" />
                  <stop offset="100%" stopColor="rgba(0,229,255,0)" />
                </linearGradient>
              </defs>
              {[
                [410,160,100,75,  0],
                [410,160,195,255, 0.6],
                [410,160,335,50,  1.2],
                [410,160,665,60,  0.4],
                [410,160,720,200, 1],
                [410,160,565,260, 1.6],
                [410,160,140,215, 0.8],
              ].map(([x1,y1,x2,y2,delay],i) => (
                <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="url(#nl)" strokeWidth=".9"
                  style={{ animation: `ray-fade 4s ease-in-out ${delay}s infinite` }} />
              ))}
              <line x1="100" y1="75"  x2="335" y2="50"  stroke="rgba(255,45,85,.1)"   strokeWidth=".7" />
              <line x1="665" y1="60"  x2="720" y2="200" stroke="rgba(234,128,252,.1)" strokeWidth=".7" />
              <line x1="195" y1="255" x2="565" y2="260" stroke="rgba(0,229,255,.08)"  strokeWidth=".7" />
            </svg>

            {/* nodes */}
            {[
              { label: 'MIRROR', x: '50%', y: '50%', size: 52, tx: '-50%', ty: '-50%', grad: 'conic-gradient(from 0deg,rgba(0,229,255,.9),rgba(234,128,252,.75),rgba(255,45,85,.85),rgba(0,229,255,.9))', ns: '4.5s', fs: '7s', fd: '0s' },
              { label: 'Pelosi',  x: '12%', y: '23%', size: 26, grad: 'conic-gradient(from 0deg,rgba(255,45,85,.9),rgba(234,128,252,.8),rgba(255,45,85,.9))',             ns: '6s',   fs: '5s',   fd: '-1s' },
              { label: 'Buffett', x: '24%', y: '80%', size: 22, grad: 'conic-gradient(from 0deg,rgba(0,229,255,.9),rgba(68,138,255,.8),rgba(0,229,255,.9))',             ns: '5s',   fs: '6.5s', fd: '-3s' },
              { label: 'Burry',   x: '41%', y: '16%', size: 18, grad: 'conic-gradient(from 0deg,rgba(0,230,118,.9),rgba(0,229,255,.8),rgba(0,230,118,.9))',             ns: '4.5s', fs: '4.5s', fd: '-2s' },
              { label: 'Musk',    x: '81%', y: '19%', size: 24, grad: 'conic-gradient(from 0deg,rgba(234,128,252,.9),rgba(68,138,255,.8),rgba(0,229,255,.9),rgba(234,128,252,.9))', ns: '7s', fs: '7s', fd: '-4s' },
              { label: 'Ackman',  x: '88%', y: '63%', size: 20, grad: 'conic-gradient(from 0deg,rgba(255,45,85,.9),rgba(255,107,0,.8),rgba(234,128,252,.7),rgba(255,45,85,.9))',    ns: '5.5s', fs: '5.5s', fd: '-.5s' },
              { label: 'Tepper',  x: '69%', y: '81%', size: 18, grad: 'conic-gradient(from 0deg,rgba(0,229,255,.9),rgba(0,230,118,.8),rgba(0,229,255,.9))',             ns: '6s',   fs: '6s',   fd: '-2.5s' },
              { label: 'Collins', x: '17%', y: '67%', size: 16, grad: 'conic-gradient(from 0deg,rgba(68,138,255,.9),rgba(234,128,252,.8),rgba(68,138,255,.9))',         ns: '5s',   fs: '5s',   fd: '-3.5s' },
            ].map((n) => (
              <div
                key={n.label}
                className="absolute flex flex-col items-center"
                style={{
                  left: n.x, top: n.y,
                  transform: `translate(${n.tx ?? '-50%'},${n.ty ?? '-50%'})`,
                  animation: `float-y ${n.fs} ease-in-out ${n.fd} infinite`,
                }}
              >
                <div
                  className="clip-prism relative overflow-hidden"
                  style={{ width: n.size, height: n.size, background: '#03070d' }}
                >
                  <div
                    className="holo-layer-sm"
                    style={{ background: n.grad, animationDuration: n.ns }}
                  />
                </div>
                <span className="mt-1 font-mono text-[0.52rem] uppercase tracking-[0.08em]" style={{ color: 'rgba(255,255,255,0.42)' }}>{n.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <SpecRule />

      {/* ── FEATURES ── */}
      <section id="roster" className="border-b py-28" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
        <div className="mx-auto max-w-[1160px] px-14">
          <div ref={addReveal} className="reveal">
            <SectionLabel>Platform Features</SectionLabel>
            <h2 className="font-barlow-condensed text-[clamp(2.1rem,4.5vw,3.9rem)] font-light leading-[1.04]" style={{ maxWidth: 480 }}>
              Everything you need<br />to mirror smart money
            </h2>
          </div>

          <div
            ref={addReveal}
            className="reveal d1 mt-14 grid grid-cols-1 md:grid-cols-2"
            style={{ border: '1px solid rgba(255,255,255,0.07)', borderRight: 'none', borderBottom: 'none' }}
          >
            {[
              { color: 'conic-gradient(from 0deg,#ff2d55,#00e5ff,#ea80fc,#ff2d55)',      name: 'Permissionless Signal Feed',    desc: 'Live signal cards for every detected insider trade — with conviction scores, sector tags, and one-click approve or skip.' },
              { color: 'conic-gradient(from 0deg,#00e5ff,#448aff,#ea80fc,#00e5ff)',      name: 'Real-time Position Tracking',   desc: 'Alpaca positions with unrealized P&L, stop-loss distance, entry tracking, and one-click exit with confirmation.' },
              { color: 'conic-gradient(from 0deg,#00e676,#00e5ff,#448aff,#00e676)',      name: 'AI Conviction Scoring',         desc: 'Each signal is scored 0–10 based on trade size, timing, historical accuracy, and AI-assessed context from Gemini.' },
              { color: 'conic-gradient(from 0deg,#ff6b00,#ffd60a,#ff2d55,#ff6b00)',     name: 'Dynamic Roster Management',     desc: 'Add or remove insiders from your mirror list. Review weekly AI proposals. Weight each member\'s influence independently.' },
              { color: 'conic-gradient(from 0deg,#ea80fc,#ff2d55,#ff6b00,#ea80fc)',     name: 'Risk-weighted Sizing',          desc: 'Position size is calculated dynamically per signal confidence, sector cap, and your portfolio\'s current exposure.' },
              { color: 'conic-gradient(from 0deg,#448aff,#00e5ff,#00e676,#448aff)',     name: 'Veto Window Protection',        desc: 'In controlled mode, every trade waits 2 hours for your veto. Full autonomy mode executes immediately on high-confidence signals.' },
            ].map((f) => (
              <div
                key={f.name}
                className="feat-item p-8"
                style={{ borderRight: '1px solid rgba(255,255,255,0.07)', borderBottom: '1px solid rgba(255,255,255,0.07)' }}
              >
                <div className="clip-diamond mb-5" style={{ width: 13, height: 13, background: f.color }} />
                <div className="mb-2.5 font-barlow-condensed text-[0.92rem] font-medium uppercase tracking-[0.07em]">{f.name}</div>
                <p className="text-[0.84rem] font-light leading-[1.72]" style={{ color: 'rgba(255,255,255,0.42)' }}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <SpecRule />

      {/* ── CTA ── */}
      <section id="docs" className="relative overflow-hidden py-40 text-center">
        {/* bg glow */}
        <div className="pointer-events-none absolute" style={{ top: '50%', left: '50%', transform: 'translate(-50%,-50%)', width: 700, height: 420, background: 'radial-gradient(ellipse,rgba(110,0,240,.11),rgba(0,229,255,.05),transparent 68%)', filter: 'blur(70px)' }} />

        <div className="relative mx-auto max-w-[1160px] px-14">
          {/* crystal above heading */}
          <div ref={addReveal} className="reveal mb-12 flex justify-center">
            <div className="relative" style={{ animation: 'float-y 7s ease-in-out infinite' }}>
              <div className="pointer-events-none absolute" style={{ top: '50%', left: '50%', transform: 'translate(-50%,-50%)', width: 200, height: 200, background: 'radial-gradient(ellipse,rgba(110,0,240,.18),transparent 68%)', filter: 'blur(28px)', animation: 'glow-pulse 4s ease-in-out infinite' }} />
              <Prism
                w={80} h={108}
                holoGradient="conic-gradient(from 0deg at 50% 50%,transparent,rgba(255,45,85,.9) 12deg,rgba(0,229,255,.9) 42deg,rgba(234,128,252,.8) 72deg,transparent 95deg,transparent 360deg)"
                spinDur="5s"
              />
            </div>
          </div>

          <h2 ref={addReveal} className="reveal mx-auto mb-11 font-barlow-condensed font-light leading-[1.02]" style={{ fontSize: 'clamp(2.4rem,6.5vw,5.2rem)', letterSpacing: '-0.015em', maxWidth: 760 }}>
            Start your mirror journey<br />and capture the edge
          </h2>

          <div ref={addReveal} className="reveal d1 mb-20 flex flex-wrap items-center justify-center gap-4">
            <a href="#" className="bg-white px-8 py-3 font-barlow text-[0.72rem] font-semibold uppercase tracking-[0.12em] text-black no-underline hover:opacity-90">Launch Dashboard</a>
            <a href="#" className="px-8 py-3 font-barlow text-[0.72rem] font-medium uppercase tracking-[0.12em] no-underline transition-colors" style={{ color: 'rgba(255,255,255,0.42)', border: '1px solid rgba(255,255,255,0.14)' }}>Read the Docs</a>
          </div>

          {/* Dashboard mockup */}
          <div ref={addReveal} className="reveal d2 relative mx-auto overflow-hidden" style={{ maxWidth: 840, border: '1px solid rgba(255,255,255,0.14)', background: '#030a14' }}>
            <div className="pointer-events-none absolute bottom-0 left-0 right-0" style={{ height: '55%', background: 'linear-gradient(to bottom,transparent,#000)' }} />
            {/* title bar */}
            <div className="flex items-center gap-2.5 border-b px-5 py-2.5" style={{ background: '#071020', borderColor: 'rgba(255,255,255,0.07)' }}>
              <span className="inline-block h-2 w-2 rounded-full bg-[#ff2d55]" />
              <span className="inline-block h-2 w-2 rounded-full bg-[#ffd60a]" />
              <span className="inline-block h-2 w-2 rounded-full bg-[#00e676]" />
              <span className="ml-2 font-mono text-[0.58rem] tracking-[0.07em]" style={{ color: 'rgba(255,255,255,0.42)' }}>mirror-ai.app — Dashboard</span>
            </div>
            {/* tabs */}
            <div className="flex overflow-x-auto border-b" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
              {['📊 Dashboard','📡 Feed','💼 Positions','👥 Roster','🏆 Leaderboard','👁 Watchlist','📋 Logs'].map((t, i) => (
                <div key={t} className="flex-shrink-0 border-r px-5 py-2.5 font-mono text-[0.6rem] uppercase tracking-[0.08em] whitespace-nowrap" style={{ borderColor: 'rgba(255,255,255,0.07)', color: i === 0 ? '#00e676' : 'rgba(255,255,255,0.42)', background: i === 0 ? 'rgba(0,230,118,0.035)' : 'transparent' }}>
                  {t}
                </div>
              ))}
            </div>
            {/* body */}
            <div className="grid grid-cols-1 md:grid-cols-[210px_1fr]" style={{ minHeight: 290 }}>
              <div className="border-r p-5" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
                <div className="mb-5 font-syncopate text-[0.6rem] font-bold uppercase tracking-[0.15em]" style={{ color: 'rgba(255,255,255,0.3)' }}>🪞 MIRROR AI</div>
                {[['Portfolio','$24,830',''],['Today P&L','+$412','#00e676'],['Buying Power','$18,240','']].map(([l,v,c]) => (
                  <div key={l} className="mb-5">
                    <div className="mb-0.5 font-mono text-[0.52rem] uppercase tracking-[0.12em]" style={{ color: 'rgba(255,255,255,0.42)' }}>{l}</div>
                    <div className="font-barlow-condensed text-[1.55rem] font-light tracking-[-0.02em]" style={{ color: c || '#fff' }}>{v}</div>
                  </div>
                ))}
                <div className="mt-2 inline-block px-3 py-1 font-mono text-[0.56rem] tracking-[0.08em]" style={{ color: '#00e676', border: '1px solid rgba(0,230,118,0.22)', background: 'rgba(0,230,118,0.04)' }}>🔒 CONTROLLED</div>
              </div>
              <div className="p-5">
                <div className="mb-3.5 font-mono text-[0.57rem] uppercase tracking-[0.1em]" style={{ color: 'rgba(255,255,255,0.42)' }}>📡 Live Signals — 3 pending</div>
                {[
                  { ticker: '$NVDA', name: 'Nancy Pelosi · 8.2% portfolio', score: 'Score 8.71', sc: '#00e5ff', tag: 'BUY · Technology' },
                  { ticker: '$TSLA', name: 'Elon Musk · 12.4% portfolio',   score: 'Score 7.45', sc: '#00e5ff', tag: 'BUY · Auto / Energy' },
                  { ticker: '$AAPL', name: 'Bill Ackman · 5.1% portfolio',  score: 'Score 6.20', sc: '#ffd60a', tag: 'BUY · Technology' },
                ].map((s) => (
                  <div key={s.ticker} className="mb-2 flex items-center justify-between border p-4" style={{ background: '#07101f', borderColor: 'rgba(255,255,255,0.07)' }}>
                    <div>
                      <div className="font-barlow-condensed text-[1.05rem] font-semibold" style={{ color: '#00e676' }}>{s.ticker}</div>
                      <div className="mt-0.5 text-[0.68rem]" style={{ color: 'rgba(255,255,255,0.42)' }}>{s.name}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-mono text-[0.66rem]" style={{ color: s.sc }}>{s.score}</div>
                      <div className="mt-0.5 text-[0.6rem]" style={{ color: 'rgba(255,255,255,0.42)' }}>{s.tag}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="flex flex-wrap items-center justify-between gap-4 border-t px-14 py-10" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
        <div className="font-syncopate text-[0.68rem] font-bold uppercase tracking-[0.2em]" style={{ color: 'rgba(255,255,255,0.42)' }}>MIRROR AI</div>
        <ul className="flex list-none gap-8">
          {['Dashboard','Docs','GitHub','Railway'].map((l) => (
            <li key={l}>
              <a href="#" className="text-[0.72rem] no-underline transition-colors" style={{ color: 'rgba(255,255,255,0.42)', letterSpacing: '0.05em' }}
                onMouseEnter={(e) => (e.currentTarget.style.color = '#fff')}
                onMouseLeave={(e) => (e.currentTarget.style.color = 'rgba(255,255,255,0.42)')}
              >{l}</a>
            </li>
          ))}
        </ul>
        <div className="font-mono text-[0.58rem] uppercase tracking-[0.08em]" style={{ color: 'rgba(255,255,255,0.18)' }}>© 2026 Mirror AI · Paper trading only.</div>
      </footer>
    </>
  )
}
