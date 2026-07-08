import React, { useState, useEffect } from 'react'
import { 
  History, Heart, User, Crown, Play, Clock, 
  Film, Loader2, ExternalLink, Trash2
} from 'lucide-react'
import { generationApi, directorsApi } from '../utils/api'
import { useAuth } from '../contexts/AuthContext'

export default function Dashboard() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('generations')
  const [generations, setGenerations] = useState([])
  const [favorites, setFavorites] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [activeTab])

  const loadData = async () => {
    setLoading(true)
    try {
      if (activeTab === 'generations') {
        const response = await generationApi.history()
        setGenerations(response.generations || [])
      } else if (activeTab === 'favorites') {
        const response = await directorsApi.getFavorites()
        setFavorites(response.map(f => f.director).filter(Boolean))
      }
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const tabs = [
    { id: 'generations', label: 'My Generations', icon: History },
    { id: 'favorites', label: 'Favorites', icon: Heart },
    { id: 'profile', label: 'Profile', icon: User }
  ]

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold">Dashboard</h2>
          <p className="text-gray-500 mt-1">Welcome back, {user?.full_name || user?.email}</p>
        </div>
        {user?.is_premium && (
          <div className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-yellow-500/20 to-orange-500/20 border border-yellow-500/50 rounded-xl">
            <Crown className="w-5 h-5 text-yellow-500" />
            <span className="font-medium text-yellow-400">Premium</span>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid sm:grid-cols-3 gap-4">
        <div className="card">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-orange-500/20 rounded-xl flex items-center justify-center">
              <Play className="w-6 h-6 text-orange-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{generations.length}</p>
              <p className="text-sm text-gray-500">Videos Generated</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-red-500/20 rounded-xl flex items-center justify-center">
              <Heart className="w-6 h-6 text-red-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{favorites.length}</p>
              <p className="text-sm text-gray-500">Favorite Directors</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-blue-500/20 rounded-xl flex items-center justify-center">
              <Film className="w-6 h-6 text-blue-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">
                {user?.is_premium ? 'Unlimited' : '5/day'}
              </p>
              <p className="text-sm text-gray-500">Daily Limit</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-800">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-orange-500 text-orange-400'
                : 'border-transparent text-gray-500 hover:text-gray-300'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-orange-500" />
        </div>
      ) : (
        <>
          {/* Generations */}
          {activeTab === 'generations' && (
            <div className="space-y-4">
              {generations.length === 0 ? (
                <div className="card text-center py-12">
                  <Film className="w-16 h-16 text-gray-700 mx-auto mb-4" />
                  <h3 className="text-xl font-bold mb-2">No generations yet</h3>
                  <p className="text-gray-500">Start creating videos to see them here</p>
                </div>
              ) : (
                generations.map(gen => (
                  <div key={gen.job_id} className="card hover:border-gray-700 transition-colors">
                    <div className="flex gap-4">
                      {/* Thumbnail */}
                      <div className="w-32 h-20 bg-gray-800 rounded-xl overflow-hidden flex-shrink-0">
                        {gen.thumbnail_url ? (
                          <img
                            src={gen.thumbnail_url}
                            alt="Thumbnail"
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <Film className="w-8 h-8 text-gray-700" />
                          </div>
                        )}
                      </div>
                      
                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="font-semibold">{gen.director_name}</h3>
                            <p className="text-sm text-gray-500">
                              {gen.scene_count} scenes • {gen.estimated_duration}s
                            </p>
                          </div>
                          <StatusBadge status={gen.status} progress={gen.progress} />
                        </div>
                        <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {new Date(gen.created_at).toLocaleDateString()}
                          </span>
                          {gen.video_url && (
                            <a
                              href={gen.video_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-orange-400 hover:text-orange-300 flex items-center gap-1"
                            >
                              View <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    {/* Progress bar */}
                    {gen.status === 'processing' && (
                      <div className="mt-4">
                        <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-orange-500 transition-all"
                            style={{ width: `${gen.progress || 0}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {/* Favorites */}
          {activeTab === 'favorites' && (
            <div className="space-y-4">
              {favorites.length === 0 ? (
                <div className="card text-center py-12">
                  <Heart className="w-16 h-16 text-gray-700 mx-auto mb-4" />
                  <h3 className="text-xl font-bold mb-2">No favorites yet</h3>
                  <p className="text-gray-500">Save directors you love to find them easily</p>
                </div>
              ) : (
                <div className="grid sm:grid-cols-2 gap-4">
                  {favorites.map(director => (
                    <div key={director.id} className="card flex gap-4">
                      <div className="w-20 h-20 bg-gray-800 rounded-xl overflow-hidden flex-shrink-0">
                        {director.image_url ? (
                          <img
                            src={director.image_url}
                            alt={director.name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <Film className="w-8 h-8 text-gray-700" />
                          </div>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold truncate">{director.name}</h3>
                        <p className="text-sm text-gray-500">{director.country}</p>
                        <div className="flex gap-1 mt-2">
                          {director.color_palette?.slice(0, 4).map((color, i) => (
                            <div
                              key={i}
                              className="w-5 h-5 rounded"
                              style={{ backgroundColor: color }}
                            />
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Profile */}
          {activeTab === 'profile' && (
            <div className="card space-y-6">
              <div className="flex items-center gap-4">
                <div className="w-20 h-20 bg-gradient-to-br from-orange-500 to-orange-600 rounded-2xl flex items-center justify-center text-3xl font-bold">
                  {(user?.full_name || user?.email)[0].toUpperCase()}
                </div>
                <div>
                  <h3 className="text-xl font-bold">{user?.full_name || 'No name set'}</h3>
                  <p className="text-gray-500">{user?.email}</p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex justify-between py-2 border-b border-gray-800">
                  <span className="text-gray-500">Account Type</span>
                  <span className={user?.is_premium ? 'text-yellow-400' : 'text-gray-300'}>
                    {user?.is_premium ? 'Premium' : 'Free'}
                  </span>
                </div>
                <div className="flex justify-between py-2 border-b border-gray-800">
                  <span className="text-gray-500">Email</span>
                  <span className="text-gray-300">{user?.email}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-gray-800">
                  <span className="text-gray-500">Member Since</span>
                  <span className="text-gray-300">
                    {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-gray-500">Daily Generations</span>
                  <span className="text-gray-300">
                    {user?.is_premium ? 'Unlimited' : '5 remaining'}
                  </span>
                </div>
              </div>

              {!user?.is_premium && (
                <button className="btn-primary w-full flex items-center justify-center gap-2">
                  <Crown className="w-5 h-5" />
                  Upgrade to Premium
                </button>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}

function StatusBadge({ status, progress }) {
  const styles = {
    completed: 'bg-green-500/20 text-green-400',
    processing: 'bg-orange-500/20 text-orange-400',
    pending: 'bg-gray-500/20 text-gray-400',
    failed: 'bg-red-500/20 text-red-400'
  }

  return (
    <span className={`px-3 py-1 rounded-full text-xs font-medium ${styles[status] || styles.pending}`}>
      {status === 'processing' ? `${progress || 0}%` : status}
    </span>
  )
}
