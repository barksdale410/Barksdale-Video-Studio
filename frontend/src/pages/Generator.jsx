import React, { useState, useEffect } from 'react'
import { 
  Play, Film, Sparkles, Loader2, CheckCircle, ChevronDown, 
  RefreshCw, Settings, PlayCircle, SkipForward, Zap
} from 'lucide-react'
import { directorsApi, analysisApi, generationApi } from '../utils/api'
import { useAuth } from '../contexts/AuthContext'

const STEPS = [
  { id: 'queued', label: 'Queued', icon: Settings },
  { id: 'parsing', label: 'Parsing', icon: Film },
  { id: 'theming', label: 'Theming', icon: Sparkles },
  { id: 'styling', label: 'Styling', icon: Sparkles },
  { id: 'generating', label: 'Generating', icon: Zap },
  { id: 'finalizing', label: 'Finalizing', icon: RefreshCw },
  { id: 'completed', label: 'Ready', icon: CheckCircle }
]

export default function Generator() {
  const { token } = useAuth()
  const [directors, setDirectors] = useState([])
  const [genres, setGenres] = useState([])
  const [moods, setMoods] = useState([])
  const [selectedDirector, setSelectedDirector] = useState(null)
  const [selectedGenre, setSelectedGenre] = useState('')
  const [selectedMood, setSelectedMood] = useState('')
  const [script, setScript] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generationJob, setGenerationJob] = useState(null)
  const [showApiConfig, setShowApiConfig] = useState(false)
  const [apiUrl, setApiUrl] = useState(localStorage.getItem('API_URL') || 'http://localhost:8001')

  useEffect(() => {
    loadFilters()
  }, [])

  const loadFilters = async () => {
    try {
      const [directorsRes, genresRes, moodsRes] = await Promise.all([
        directorsApi.list({ limit: 100, sort_by: 'popularity_score', sort_order: 'desc' }),
        directorsApi.getGenres(),
        directorsApi.getMoods()
      ])
      setDirectors(directorsRes.directors || [])
      setGenres(genresRes.genres || [])
      setMoods(moodsRes.moods || [])
    } catch (error) {
      console.error('Failed to load filters:', error)
    }
  }

  const handleAnalyze = async () => {
    if (!script.trim()) return
    
    setIsAnalyzing(true)
    setAnalysis(null)
    
    try {
      const result = await analysisApi.analyze({
        script,
        director_id: selectedDirector?.id,
        director_name: selectedDirector?.name,
        genre: selectedGenre,
        mood: selectedMood
      })
      setAnalysis(result)
    } catch (error) {
      console.error('Analysis failed:', error)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleGenerate = async () => {
    if (!selectedDirector) {
      alert('Please select a director first')
      return
    }
    
    setIsGenerating(true)
    setGenerationJob(null)
    
    try {
      const result = await generationApi.start({
        script,
        director_id: selectedDirector.id,
        genre: selectedGenre,
        mood: selectedMood,
        analysis_id: analysis?.analysis_id
      })
      setGenerationJob(result)
      
      // Poll for status
      pollJobStatus(result.job_id)
    } catch (error) {
      console.error('Generation failed:', error)
      setIsGenerating(false)
    }
  }

  const pollJobStatus = async (jobId) => {
    const poll = async () => {
      try {
        const status = await generationApi.status(jobId)
        setGenerationJob(status)
        
        if (status.status === 'completed' || status.status === 'failed') {
          setIsGenerating(false)
        } else {
          setTimeout(poll, 2000)
        }
      } catch (error) {
        console.error('Status check failed:', error)
        setTimeout(poll, 5000)
      }
    }
    poll()
  }

  const getCurrentStepIndex = () => {
    if (!generationJob) return -1
    const stepMap = {
      'pending': 0,
      'processing': STEPS.findIndex(s => s.id === generationJob.current_step?.toLowerCase()) || 1,
      'completed': STEPS.length - 1
    }
    return stepMap[generationJob.status] ?? 1
  }

  const saveApiUrl = () => {
    localStorage.setItem('API_URL', apiUrl)
    setShowApiConfig(false)
    window.location.reload()
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <h2 className="text-4xl font-bold gradient-text">AI Video Generator</h2>
        <p className="text-gray-400 max-w-2xl mx-auto">
          Transform your script into a cinematic storyboard with the style of legendary directors
        </p>
      </div>

      {/* API Config */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Settings className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-500">API: {apiUrl}</span>
          </div>
          <button
            onClick={() => setShowApiConfig(!showApiConfig)}
            className="text-sm text-orange-400 hover:text-orange-300"
          >
            {showApiConfig ? 'Hide' : 'Configure'}
          </button>
        </div>
        {showApiConfig && (
          <div className="mt-4 flex gap-2">
            <input
              type="text"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              placeholder="https://your-api.onrender.com"
              className="input-field flex-1"
            />
            <button onClick={saveApiUrl} className="btn-secondary">
              Save
            </button>
          </div>
        )}
      </div>

      {/* Main form */}
      <div className="grid lg:grid-cols-2 gap-8">
        {/* Left: Inputs */}
        <div className="space-y-6">
          {/* Director selection */}
          <div className="card">
            <label className="block text-sm font-medium text-gray-400 mb-3">
              🎬 Select Director
            </label>
            <select
              value={selectedDirector?.id || ''}
              onChange={(e) => {
                const director = directors.find(d => d.id === parseInt(e.target.value))
                setSelectedDirector(director || null)
              }}
              className="select-field"
            >
              <option value="">Choose a legendary director...</option>
              {directors.map((director) => (
                <option key={director.id} value={director.id}>
                  {director.name} ({director.popularity_score?.toFixed(1)}⭐)
                </option>
              ))}
            </select>
            
            {selectedDirector && (
              <div className="mt-4 p-4 bg-gray-800/50 rounded-xl">
                <div className="flex items-start gap-4">
                  {selectedDirector.color_palette?.length > 0 && (
                    <div className="flex gap-1">
                      {selectedDirector.color_palette.slice(0, 4).map((color, i) => (
                        <div
                          key={i}
                          className="w-8 h-8 rounded-lg border border-gray-700"
                          style={{ backgroundColor: color }}
                        />
                      ))}
                    </div>
                  )}
                  <div className="flex-1">
                    <h4 className="font-semibold">{selectedDirector.name}</h4>
                    <p className="text-sm text-gray-400 mt-1">
                      {selectedDirector.visual_signature || selectedDirector.style}
                    </p>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {selectedDirector.moods?.slice(0, 4).map((mood, i) => (
                        <span key={i} className="px-2 py-0.5 bg-gray-700 rounded text-xs">
                          {mood}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Genre & Mood */}
          <div className="grid sm:grid-cols-2 gap-4">
            <div className="card">
              <label className="block text-sm font-medium text-gray-400 mb-3">
                🎭 Genre
              </label>
              <select
                value={selectedGenre}
                onChange={(e) => setSelectedGenre(e.target.value)}
                className="select-field"
              >
                <option value="">Any Genre</option>
                {genres.map((genre) => (
                  <option key={genre} value={genre}>{genre}</option>
                ))}
              </select>
            </div>
            <div className="card">
              <label className="block text-sm font-medium text-gray-400 mb-3">
                🎨 Mood
              </label>
              <select
                value={selectedMood}
                onChange={(e) => setSelectedMood(e.target.value)}
                className="select-field"
              >
                <option value="">Any Mood</option>
                {moods.map((mood) => (
                  <option key={mood} value={mood}>{mood}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Script input */}
          <div className="card">
            <label className="block text-sm font-medium text-gray-400 mb-3">
              📝 Your Script
            </label>
            <textarea
              value={script}
              onChange={(e) => setScript(e.target.value)}
              placeholder="Paste your script here...

Example:
INT. DARK STUDIO - NIGHT

A lone producer sits at a mixing console. Neon lights flicker.

PRODUCER
(whispering)
The beat is almost ready."
              className="input-field min-h-[300px] font-mono text-sm"
            />
          </div>

          {/* Analyze button */}
          <button
            onClick={handleAnalyze}
            disabled={!script.trim() || isAnalyzing}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Analyze Script
              </>
            )}
          </button>
        </div>

        {/* Right: Results */}
        <div className="space-y-6">
          {/* Storyboard */}
          {analysis && (
            <div className="card animate-fade-in">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-lg">📋 Storyboard</h3>
                <span className="text-sm text-gray-500">
                  {analysis.scene_count} scenes • {analysis.total_duration}s
                </span>
              </div>
              
              <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
                {analysis.scenes.map((scene, i) => (
                  <div key={i} className="p-3 bg-gray-800/50 rounded-xl">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-orange-400">Scene {i + 1}</span>
                      <span className="text-xs text-gray-500">{scene.duration}s</span>
                    </div>
                    <div className="text-sm text-gray-300 font-medium mb-1">{scene.heading}</div>
                    <div className="text-xs text-gray-500 line-clamp-2">{scene.action}</div>
                    {scene.camera && (
                      <div className="mt-2 flex gap-1">
                        {scene.color_palette?.map((color, j) => (
                          <div
                            key={j}
                            className="w-4 h-4 rounded"
                            style={{ backgroundColor: color }}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Generation */}
          {selectedDirector && analysis && (
            <div className="card">
              <button
                onClick={handleGenerate}
                disabled={isGenerating}
                className="btn-primary w-full relative overflow-hidden"
              >
                {isGenerating ? (
                  <>
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <PlayCircle className="w-5 h-5" />
                    Generate Video
                  </>
                )}
              </button>
            </div>
          )}

          {/* Progress */}
          {generationJob && generationJob.status !== 'completed' && generationJob.status !== 'failed' && (
            <div className="card">
              <h3 className="font-bold mb-4">Generation Progress</h3>
              <div className="space-y-4">
                <div className="flex justify-between text-sm">
                  <span>{generationJob.current_step || 'Starting...'}</span>
                  <span>{generationJob.progress || 0}%</span>
                </div>
                <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-orange-500 to-orange-600 transition-all duration-500"
                    style={{ width: `${generationJob.progress || 0}%` }}
                  />
                </div>
                <div className="flex justify-between">
                  {STEPS.slice(0, -1).map((step, i) => {
                    const currentIndex = getCurrentStepIndex()
                    const isActive = i <= currentIndex
                    const isCurrent = i === currentIndex
                    return (
                      <div
                        key={step.id}
                        className={`flex flex-col items-center ${
                          isActive ? 'text-orange-400' : 'text-gray-600'
                        }`}
                      >
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                          isCurrent ? 'bg-orange-500/20 ring-2 ring-orange-500' : ''
                        }`}>
                          <step.icon className="w-4 h-4" />
                        </div>
                        <span className="text-xs mt-1 hidden sm:block">{step.label}</span>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          )}

          {/* Completed */}
          {generationJob?.status === 'completed' && (
            <div className="card border-green-500/50 animate-fade-in">
              <div className="text-center space-y-4">
                <CheckCircle className="w-16 h-16 text-green-500 mx-auto" />
                <h3 className="text-xl font-bold">Video Ready!</h3>
                <p className="text-gray-400">
                  Your video is being rendered and will be available shortly.
                </p>
                {generationJob.video_url && (
                  <a
                    href={generationJob.video_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-primary inline-flex items-center gap-2"
                  >
                    <Play className="w-5 h-5" />
                    Watch Video
                  </a>
                )}
              </div>
            </div>
          )}

          {/* Error */}
          {generationJob?.status === 'failed' && (
            <div className="card border-red-500/50">
              <div className="text-center space-y-4">
                <p className="text-red-400 font-medium">Generation Failed</p>
                <p className="text-sm text-gray-400">{generationJob.error_message}</p>
                <button
                  onClick={handleGenerate}
                  className="btn-secondary"
                >
                  Try Again
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
