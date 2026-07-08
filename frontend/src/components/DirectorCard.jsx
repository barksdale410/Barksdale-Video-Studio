import React, { useState } from 'react'
import { Heart, Star, Film, Globe, Sparkles } from 'lucide-react'

export default function DirectorCard({ director, onSelect, onFavorite, isFavorite }) {
  const [imageError, setImageError] = useState(false)

  return (
    <div
      className="group card hover:border-orange-500/50 transition-all duration-300 cursor-pointer"
      onClick={() => onSelect(director)}
    >
      {/* Image */}
      <div className="relative aspect-[4/3] rounded-xl overflow-hidden mb-4 bg-gray-800">
        {!imageError && director.image_url ? (
          <img
            src={director.image_url}
            alt={director.name}
            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
            onError={() => setImageError(true)}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-800 to-gray-900">
            <Film className="w-12 h-12 text-gray-700" />
          </div>
        )}
        
        {/* Featured badge */}
        {director.is_featured && (
          <div className="absolute top-2 left-2 px-2 py-1 bg-orange-500 rounded-lg text-xs font-bold flex items-center gap-1">
            <Sparkles className="w-3 h-3" />
            FEATURED
          </div>
        )}
        
        {/* Favorite button */}
        <button
          onClick={(e) => {
            e.stopPropagation()
            onFavorite(director)
          }}
          className={`absolute top-2 right-2 p-2 rounded-full transition-all ${
            isFavorite
              ? 'bg-red-500 text-white'
              : 'bg-black/50 text-white/70 hover:bg-black/70 hover:text-white'
          }`}
        >
          <Heart className={`w-4 h-4 ${isFavorite ? 'fill-current' : ''}`} />
        </button>
      </div>

      {/* Content */}
      <div className="space-y-3">
        <div>
          <h3 className="font-bold text-lg group-hover:text-orange-400 transition-colors">
            {director.name}
          </h3>
          <div className="flex items-center gap-3 text-sm text-gray-500">
            {director.country && (
              <span className="flex items-center gap-1">
                <Globe className="w-3 h-3" />
                {director.country}
              </span>
            )}
            {director.birth_year && (
              <span>{director.birth_year}</span>
            )}
          </div>
        </div>

        {/* Rating and films */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1">
            <Star className="w-4 h-4 text-yellow-500 fill-current" />
            <span className="text-sm font-medium">{director.popularity_score?.toFixed(1) || 'N/A'}</span>
          </div>
          <span className="text-sm text-gray-500 flex items-center gap-1">
            <Film className="w-3 h-3" />
            {director.film_count || 0} films
          </span>
        </div>

        {/* Color palette */}
        {director.color_palette && director.color_palette.length > 0 && (
          <div className="flex gap-1">
            {director.color_palette.slice(0, 4).map((color, i) => (
              <div
                key={i}
                className="w-6 h-6 rounded-full border border-gray-700"
                style={{ backgroundColor: color }}
                title={color}
              />
            ))}
          </div>
        )}

        {/* Genres */}
        {director.genres && director.genres.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {director.genres.slice(0, 3).map((genre, i) => (
              <span
                key={i}
                className="px-2 py-1 bg-gray-800 rounded-lg text-xs text-gray-400"
              >
                {genre}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
