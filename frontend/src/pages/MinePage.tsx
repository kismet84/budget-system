import { useState, useEffect } from 'react'
import { Settings, Database, Github, ChevronRight, Loader2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import BottomNav from '../components/BottomNav'

interface Stats {
  quota_count: number
  price_count: number
  vector_index_status: string
}

const api = axios.create({
  baseURL: '',
  timeout: 15000,
})

export default function MinePage() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await api.get<Stats>('/api/v1/quota/stats')
        setStats(res.data)
      } catch (err) {
        console.error('Failed to fetch stats:', err)
        // Set default values on error
        setStats({
          quota_count: 0,
          price_count: 0,
          vector_index_status: '未知',
        })
      } finally {
        setLoading(false)
      }
    }
    fetchStats()
  }, [])

  return (
    <div className="min-h-screen bg-slate-900 pb-20">
      <div className="px-4 pt-6 pb-4">
        <h1 className="text-white text-xl font-bold mb-6">我的</h1>

        <div className="space-y-3">
          {/* Data Status */}
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Database size={20} className="text-blue-400" />
                <div>
                  <div className="text-white text-sm font-medium">数据状态</div>
                  {loading ? (
                    <div className="text-slate-400 text-xs mt-0.5 flex items-center gap-1">
                      <Loader2 size={10} className="animate-spin" />
                      加载中...
                    </div>
                  ) : (
                    <div className="text-slate-400 text-xs mt-0.5">
                      {stats?.quota_count ?? 0} 条定额 · {stats?.price_count ?? 0} 条价格
                    </div>
                  )}
                </div>
              </div>
              <button
                onClick={() => navigate('/prices')}
                className="text-slate-400 hover:text-white flex items-center gap-1 text-xs"
              >
                管理
                <ChevronRight size={14} />
              </button>
            </div>
            {stats && (
              <div className="mt-2 pt-2 border-t border-slate-700">
                <div className="text-slate-500 text-xs">
                  向量索引：{stats.vector_index_status}
                </div>
              </div>
            )}
          </div>

          {/* System Info */}
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <div className="flex items-center gap-3">
              <Github size={20} className="text-slate-400" />
              <div>
                <div className="text-white text-sm font-medium">建设工程预算分析系统</div>
                <div className="text-slate-400 text-xs mt-0.5">v1.0 · 装饰工程定额库</div>
              </div>
            </div>
          </div>

          {/* Settings */}
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
