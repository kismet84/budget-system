import { Settings, Database, Github } from 'lucide-react'
import BottomNav from '../components/BottomNav'

export default function MinePage() {
  return (
    <div className="min-h-screen bg-slate-900 pb-20">
      <div className="px-4 pt-6 pb-4">
        <h1 className="text-white text-xl font-bold mb-6">我的</h1>

        <div className="space-y-3">
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <div className="flex items-center gap-3">
              <Database size={20} className="text-blue-400" />
              <div>
                <div className="text-white text-sm font-medium">数据状态</div>
                <div className="text-slate-400 text-xs mt-0.5">1859 条定额已入库</div>
              </div>
            </div>
          </div>

          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <div className="flex items-center gap-3">
              <Github size={20} className="text-slate-400" />
              <div>
                <div className="text-white text-sm font-medium">建设工程预算分析系统</div>
                <div className="text-slate-400 text-xs mt-0.5">v1.0 · 装饰工程定额库</div>
              </div>
            </div>
          </div>

          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <div className="flex items-center gap-3">
              <Settings size={20} className="text-slate-400" />
              <div>
                <div className="text-white text-sm font-medium">设置</div>
                <div className="text-slate-400 text-xs mt-0.5">API · 服务器配置</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <BottomNav />
    </div>
  )
}
