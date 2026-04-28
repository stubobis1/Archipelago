import React, { useState, useEffect } from 'react'
import { useStore, initStoreListeners } from './store'
import { TitleBar } from './components/TitleBar'
import { Sidebar } from './components/Sidebar'
import { Onboarding } from './screens/Onboarding'
import { DashboardPage } from './screens/Dashboard'
import { GearScreen } from './screens/Gear'
import { ItemsScreen } from './screens/Items'
import { GoalScreen } from './screens/Goal'
import { LocationsScreen } from './screens/Locations'
import { SettingsScreen } from './screens/Settings'

type Screen = 'dashboard' | 'gear' | 'items' | 'locations' | 'goal' | 'settings' | 'setup'

let listenersInited = false

export function App() {
  const [screen, setScreen] = useState<Screen>('dashboard')
  const [settingsSection, setSettingsSection] = useState('')
  const { onboardingDone } = useStore()
  const [setupDone, setSetupDone] = useState(false)
  const [stateReady, setStateReady] = useState(false)

  const handleNavigate = (s: string, section?: string) => {
    setScreen(s as Screen)
    setSettingsSection(section ?? '')
  }

  useEffect(() => {
    if (!listenersInited) {
      initStoreListeners()
      listenersInited = true
    }
    // Mark ready after first state:full arrives (requestFullState is called inside initStoreListeners)
    const unsub = useStore.subscribe(() => { setStateReady(true); unsub() })
    return unsub
  }, [])

  if (!stateReady) return <div className="app"><TitleBar /></div>

  const showOnboarding = !onboardingDone && !setupDone

  if (showOnboarding) {
    return (
      <div className="app">
        <TitleBar />
        <Onboarding onDone={() => setSetupDone(true)} />
      </div>
    )
  }

  return (
    <div className="app">
      <TitleBar />
      <div className="shell">
        <Sidebar active={screen} onNavigate={s => { setScreen(s); setSettingsSection('') }} />
        <div className="content">
          {screen === 'dashboard' && <DashboardPage onNavigate={handleNavigate} />}
          {screen === 'gear'      && <GearScreen />}
          {screen === 'items'     && <ItemsScreen />}
          {screen === 'locations' && <LocationsScreen />}
          {screen === 'goal'      && <GoalScreen />}
          {screen === 'settings'  && <SettingsScreen scrollTo={settingsSection} />}
          {screen === 'setup'     && <Onboarding onDone={() => setScreen('dashboard')} />}
        </div>
      </div>
    </div>
  )
}
