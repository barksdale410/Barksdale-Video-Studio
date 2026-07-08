import React, { useState, useEffect, useCallback } from 'react'
import { 
  Search, Filter, Grid, List, ChevronDown, Shuffle, 
  Star, MapPin, Film, X, Heart, Check
} from 'lucide-react'
import DirectorCard from '../components/DirectorCard'
import { directorsApi } from '../utils/api'
import { useAuth } from '../contexts/AuthContext'

const ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')

export default function DirectorLibrary() {
  const { token } = useAuth()
  const [directors, setDirectors] = useState([])
  const [letters, setLetters] = useState([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  
  // Filters
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedLetter, setSelectedLetter] = useState('')
  const [selectedGenre, setSelectedGenre] = useState('')
  const [selectedMood, setSelectedMood] = useState('')
  const [selectedCountry, setSelectedCountry] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  const [viewMode, setViewMode] = useState('grid') // grid or list
  
  // Genres and moods for filter options
  const [genres, setGenres] = useState([])
  const [moods, setMoods] = useState([])
  const [countries, setCountries] = useState([])
  
  // Favorites
  const [favorites, setFavorites] = useState([])
  const [selectedDirector, setSelectedDirector] = useState(null)

  useEffect(() => {
    loadFilters()
    if (token) loadFavorites()
  }, [token])

  useEffect(() => {
    loadDirectors()
  }, [selectedLetter, selectedGenre, selectedMood, selectedCountry, searchQuery, page])

  const loadFilters = async () => {
    try {
      const [genresRes, moodsRes, countriesRes, lettersRes] = await Promise.all([
        directorsApi.getGenres(),
        directorsApi.getMoods(),
        directorsApi.getCountries(),
        directorsApi.getLetters()
      ])
      setGenres(genresRes.genres || [])
      setMoods(moodsRes.moods || [])
      setCountries(countriesRes.countries || [])
      setLetters(lettersRes.letters || [])
    } catch (error) {
      console.error('Failed to load filters:', error)
    }
  }

  const loadDirectors = async () => {
    setLoading(true)
    try {
      const params = {
        page,
        limit: 24,
        sort_by: 'popularity_score',
        sort_order: 'desc'
      }
      
      if (selectedLetter) params.letter = selectedLetter
      if (selectedGenre) params.genre = selectedGenre
      if (selectedMood) params.mood = selectedMood
      if (selectedCountry) params.country = selectedCountry
      if (searchQuery) params.search = searchQuery
      
      const response = await directorsApi.list(params)
      setDirectors(response.directors || [])
      setTotalPages(response.total_pages || 1)
    } catch (error) {
      console.error('Failed to load directors:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadFavorites = async () => {
    try {
      const response = await directorsApi.getFavorites()
      setFavorites(response.map(f => f.director?.id || f.director_id))
    } catch (error) {
      console.error('Failed to load favorites:', error)
    }
  }

  const handleSearch = useCallback((e) => {
    e.preventDefault()
    setPage(1)
    loadDirectors()
  }, [])

  const handleFavorite = async (director) => {
    if (!token) {
      alert('Please sign in to save favorites')
      return
    }
    
    const isFavorite = favorites.includes(director.id)
    
    try {
      if (isFavorite) {
        await directorsApi.removeFavorite(director.id)
        setFavorites(favorites.filter(id => id !== director.id))
      } else {
        await directorsApi.addFavorite(director.id)
        setFavorites([...favorites, director.id])
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error)
    }
  }

  const handleSurpriseMe = async () => {
    try {
      const director = await directorsApi.random({ genre: selectedGenre, mood: selectedMood })
      setSelectedDirector(director)
    } catch (error) {
      console.error('Failed to get random director:', error)
    }
  }

  const clearFilters = () => {
    setSelectedLetter('')
    setSelectedGenre('')
    setSelectedMood('')
    setSelectedCountry('')
    setSearchQuery('')
    setPage(1)
  }

  const hasActiveFilters = selectedLetter || selectedGenre || selectedMood || selectedCountry || searchQuery

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center space-y-4">
        <h2 className="text-4xl font-bold gradient-text">Director Library</h2>
        <p className="text-gray-400 max-w-2xl mx-auto">
          Explore 500+ iconic directors and their cinematic styles
        </p>
      </div>

      {/* Search and controls */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <form onSubmit={handleSearch} className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search directors by name, country, or style..."
                className="input-field pl-10"
              />
            </div>
          </form>

          {/* Actions */}
          <div className="flex gap-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`btn-secondary flex items-center gap-2 ${showFilters ? 'bg-orange-500/20 border-orange-500' : ''}`}
            >
              <Filter className="w-4 h-4" />
              Filters
              {hasActiveFilters && (
                <span className="w-2 h-2 bg-orange-500 rounded-full" />
              )}
            </button>
            <button
              onClick={handleSurpriseMe}
              className="btn-secondary flex items-center gap-2"
            >
              <Shuffle className="w-4 h-4" />
              Surprise Me
            </button>
          </div>
        </div>

        {/* Filters panel */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-gray-800 space-y-4 animate-fade-in">
            {/* Alphabet */}
            <div>
              <label className="block text-sm text-gray-500 mb-2">Starting Letter</label>
              <div className="flex flex-wrap gap-1">
                {ALPHABET.map(letter => (
                  <button
                    key={letter}
                    onClick={() => {
                      setSelectedLetter(selectedLetter === letter ? '' : letter)
                      setPage(1)
                    }}
                    className={`w-8 h-8 rounded-lg text-sm font-medium transition-colors ${
                      selectedLetter === letter
                        ? 'bg-orange-500 text-white'
                        : letters.includes(letter)
                          ? 'bg-gray-800 hover:bg-gray-700 text-gray-300'
                          : 'bg-gray-900 text-gray-600 cursor-not-allowed'
                    }`}
                    disabled={!letters.includes(letter)}
                  >
                    {letter}
                  </button>
                ))}
              </div>
            </div>

            {/* Dropdowns */}
            <div className="grid sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm text-gray-500 mb-2">Genre</label>
                <select
                  value={selectedGenre}
                  onChange={(e) => { setSelectedGenre(e.target.value); setPage(1) }}
                  className="select-field"
                >
                  <option value="">All Genres</option>
                  {genres.map(genre => (
                    <option key={genre} value={genre}>{genre}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-500 mb-2">Mood</label>
                <select
                  value={selectedMood}
                  onChange={(e) => { setSelectedMood(e.target.value); setPage(1) }}
                  className="select-field"
                >
                  <option value="">All Moods</option>
                  {moods.map(mood => (
                    <option key={mood} value={mood}>{mood}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-500 mb-2">Country</label>
                <select
                  value={selectedCountry}
                  onChange={(e) => { setSelectedCountry(e.target.value); setPage(1) }}
                  className="select-field"
                >
                  <option value="">All Countries</option>
                  {countries.map(country => (
                    <option key={country} value={country}>{country}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Clear filters */}
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="text-sm text-orange-400 hover:text-orange-300"
              >
                Clear all filters
              </button>
            )}
          </div>
        )}
      </div>

      {/* Results */}
      <div className="flex items-center justify-between">
        <p className="text-gray-500">
          {loading ? 'Loading...' : `${directors.length} directors found`}
        </p>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">View:</span>
          <button
            onClick={() => setViewMode('grid')}
            className={`p-2 rounded-lg ${viewMode === 'grid' ? 'bg-orange-500/20 text-orange-400' : 'text-gray-500'}`}
          >
            <Grid className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-2 rounded-lg ${viewMode === 'list' ? 'bg-orange-500/20 text-orange-400' : 'text-gray-500'}`}
          >
            <List className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Directors grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="aspect-[4/3] bg-gray-800 rounded-xl mb-4" />
              <div className="h-4 bg-gray-800 rounded w-3/4 mb-2" />
              <div className="h-3 bg-gray-800 rounded w-1/2" />
            </div>
          ))}
        </div>
      ) : directors.length === 0 ? (
        <div className="card text-center py-12">
          <Film className="w-16 h-16 text-gray-700 mx-auto mb-4" />
          <h3 className="text-xl font-bold mb-2">No directors found</h3>
          <p className="text-gray-500">Try adjusting your filters or search query</p>
        </div>
      ) : (
        <div className={`grid gap-6 ${
          viewMode === 'grid'
            ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'
            : 'grid-cols-1'
        }`}>
          {directors.map(director => (
            <DirectorCard
              key={director.id}
              director={director}
              onSelect={setSelectedDirector}
              onFavorite={handleFavorite}
              isFavorite={favorites.includes(director.id)}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="btn-secondary"
          >
            Previous
          </button>
          <span className="px-4 py-2 text-gray-400">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
            className="btn-secondary"
          >
            Next
          </button>
        </div>
      )}

      {/* Director detail modal */}
      {selectedDirector && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80" onClick={() => setSelectedDirector(null)}>
          <div className="card max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-2xl font-bold">{selectedDirector.name}</h3>
                <div className="flex items-center gap-3 text-gray-500 mt-1">
                  {selectedDirector.country && <span>{selectedDirector.country}</span>}
                  {selectedDirector.birth_year && <span>{selectedDirector.birth_year}</span>}
                </div>
              </div>
              <button
                onClick={() => setSelectedDirector(null)}
                className="p-2 hover:bg-gray-800 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Color palette */}
            {selectedDirector.color_palette?.length > 0 && (
              <div className="mb-4">
                <h4 className="text-sm text-gray-500 mb-2">Color Palette</h4>
                <div className="flex gap-2">
                  {selectedDirector.color_palette.map((color, i) => (
                    <div
                      key={i}
                      className="w-12 h-12 rounded-xl border border-gray-700"
                      style={{ backgroundColor: color }}
                      title={color}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Styles */}
            <div className="space-y-4">
              {selectedDirector.camera_style && (
                <div>
                  <h4 className="text-sm text-gray-500">Camera</h4>
                  <p>{selectedDirector.camera_style}</p>
                </div>
              )}
              {selectedDirector.lighting_style && (
                <div>
                  <h4 className="text-sm text-gray-500">Lighting</h4>
                  <p>{selectedDirector.lighting_style}</p>
                </div>
              )}
              {selectedDirector.editing_style && (
                <div>
                  <h4 className="text-sm text-gray-500">Editing</h4>
                  <p>{selectedDirector.editing_style}</p>
                </div>
              )}
              {selectedDirector.sound_style && (
                <div>
                  <h4 className="text-sm text-gray-500">Sound</h4>
                  <p>{selectedDirector.sound_style}</p>
                </div>
              )}
              {selectedDirector.visual_signature && (
                <div>
                  <h4 className="text-sm text-gray-500">Visual Signature</h4>
                  <p className="italic">{selectedDirector.visual_signature}</p>
                </div>
              )}
            </div>

            {/* Tags */}
            <div className="mt-6 flex flex-wrap gap-2">
              {selectedDirector.moods?.map((mood, i) => (
                <span key={i} className="px-3 py-1 bg-gray-800 rounded-full text-sm">
                  {mood}
                </span>
              ))}
              {selectedDirector.genres?.map((genre, i) => (
                <span key={i} className="px-3 py-1 bg-orange-500/20 text-orange-400 rounded-full text-sm">
                  {genre}
                </span>
              ))}
            </div>

            {/* Actions */}
            <div className="mt-6 flex gap-3">
              <button
                onClick={() => handleFavorite(selectedDirector)}
                className={`flex-1 btn-secondary flex items-center justify-center gap-2 ${
                  favorites.includes(selectedDirector.id) ? '!border-red-500 !text-red-400' : ''
                }`}
              >
                <Heart className={`w-4 h-4 ${favorites.includes(selectedDirector.id) ? 'fill-current' : ''}`} />
                {favorites.includes(selectedDirector.id) ? 'Saved' : 'Save'}
              </button>
              <button className="flex-1 btn-primary flex items-center justify-center gap-2">
                Use This Director
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
