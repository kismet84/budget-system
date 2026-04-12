import { Search, FolderOpen, User } from 'lucide-react'
import { useNavigate, useLocation } from 'react-router-dom'

export default function BottomNav() {
  const navigate = useNavigate()
  const location = useLocation()

  const tabs = [
    { icon: Search, label: '搜索', path: '/' },
    { icon: FolderOpen, label: '项目', path: '/cart' },
    { icon: User, label: '我的', path: '/mine' },
  ]

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-slate-800 border-t border-slate-700 flex justify-around items-center h-14 px-4 z-50">
      {tabs.map(({ icon: Icon, label, path }) => (
        <button
          key={path}
          onClick={() => navigate(path)}
          className={`flex flex-col items-center gap-0.5 py-1 px-4 rounded-lg transition-colors ${
            location.pathname === path ? 'text-blue-400' : 'text-slate-400'
          }`}
        >
          <Icon size={20} />
          <span className="text-xs">{label}</span>
        </button>
      ))}
    </div>
  )
}
