def icon_svg(nombre: str) -> str:
    base = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" style="width: 22px; height: 22px;">'
    
    if nombre == 'sistemas_lineales':
        return base + '''
            <line x1="4" y1="20" x2="20" y2="4"></line>
            <line x1="4" y1="8" x2="20" y2="16"></line>
            <circle cx="12" cy="12" r="2.5" fill="currentColor" stroke="none"></circle>
        </svg>'''
    
    elif nombre == 'operaciones_matrices':
        return base + '''
            <path d="M7 4H5v16h2"></path>
            <path d="M17 4h2v16h-2"></path>
            <path d="M9.5 9.5l5 5m0-5l-5 5"></path>
        </svg>'''
    
    elif nombre == 'conversor_bases':
        return base + '''
            <rect x="3" y="4" width="3" height="5" rx="1"></rect>
            <line x1="8" y1="4" x2="8" y2="9"></line>
            <path d="M15 20l2.5-6 2.5 6"></path>
            <line x1="16" y1="18" x2="19" y2="18"></line>
            <path d="M12 3a9 9 0 0 1 8 5"></path>
            <polyline points="20,5 20,8 17,8"></polyline>
            <path d="M12 21a9 9 0 0 1-8-5"></path>
            <polyline points="4,19 4,16 7,16"></polyline>
        </svg>'''
    
    elif nombre == 'tutor_ia':
        return base + '''
            <path d="M2 11l9-4 9 4-9 4-9-4z"></path>
            <path d="M5 12.3v3.7c0 1.5 3.1 2.7 7 2.7s7-1.2 7-2.7v-3.7"></path>
            <path d="M19 2l1 2 2 1-2 1-1 2-1-2-2-1 2-1z" fill="currentColor" stroke="none"></path>
        </svg>'''
    
    elif nombre == 'vectores':
        return base + '''
            <line x1="5" y1="19" x2="17" y2="7"></line>
            <polyline points="9,7 17,7 17,15"></polyline>
        </svg>'''
    
    elif nombre == 'temas':
        return base + '''
            <circle cx="12" cy="12" r="8"></circle>
            <path d="M17.65 6.35A8 8 0 0 0 6.35 17.65Z" fill="currentColor" stroke="none"></path>
        </svg>'''
    
    elif nombre == 'matriz_inversa':
        return base + '''
            <path d="M6 4H4v16h2"></path>
            <path d="M12 4h2v16h-2"></path>
            <circle cx="7" cy="9" r="1" fill="currentColor" stroke="none"></circle>
            <circle cx="11" cy="15" r="1" fill="currentColor" stroke="none"></circle>
            <path d="M16.5 7h3"></path>
            <path d="M22 4.5v5"></path>
        </svg>'''
    
    elif nombre == 'inicio':
        return base + '''
            <path d="M4 11.5 12 5l8 6.5"></path>
            <path d="M6 10v9h12v-9"></path>
            <path d="M10 19v-5h4v5"></path>
        </svg>'''
    
    elif nombre == 'algebra_lineal':
        return base + '''
            <path d="M7 4H5v16h2"></path>
            <path d="M17 4h2v16h-2"></path>
            <circle cx="10" cy="9" r="1" fill="currentColor" stroke="none"></circle>
            <circle cx="14" cy="9" r="1" fill="currentColor" stroke="none"></circle>
            <circle cx="10" cy="15" r="1" fill="currentColor" stroke="none"></circle>
            <circle cx="14" cy="15" r="1" fill="currentColor" stroke="none"></circle>
        </svg>'''
    
    elif nombre == 'utilidades':
        return base + '''
            <path d="M5 8h14"></path>
            <path d="M5 16h14"></path>
            <path d="M9 4 7 20"></path>
            <path d="M17 4l-2 16"></path>
        </svg>'''
    
    elif nombre == 'geometria':
        return base + '''
            <path d="M12 3 4 7.5v9L12 21l8-4.5v-9z"></path>
            <path d="M12 12 4 7.5"></path>
            <path d="M12 12l8-4.5"></path>
            <path d="M12 12v9"></path>
        </svg>'''
    
    elif nombre == 'romanos':
        return base + '''
            <path d="M4 6h4M6 6v12M4 18h4M13 6l3.5 12 3.5-12"/>
        </svg>'''
        
    elif nombre == 'glosa':
        return base + '''
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
            <line x1="4" y1="4" x2="4" y2="20"></line>
        </svg>'''
        
    elif nombre == 'explicar_paso':
        return base + '''
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
            <line x1="12" y1="9" x2="12" y2="9.01"></line>
            <path d="M12 13v4"></path>
        </svg>'''
    
    elif nombre == 'escena_rectas_planos':
        return base + '''
            <polygon points="3 17 9 7 21 7 15 17"></polygon>
            <line x1="4" y1="18" x2="18" y2="6"></line>
            <line x1="6" y1="6" x2="16" y2="18"></line>
        </svg>'''
    
    elif nombre == 'escena_combinacion':
        return base + '''
            <line x1="4" y1="19" x2="13" y2="19"></line>
            <polyline points="10 17 13 19 10 21"></polyline>
            <line x1="4" y1="19" x2="9" y2="10"></line>
            <polyline points="6 11 9 10 10 13"></polyline>
            <path d="M9 10h9l-5 9" stroke-dasharray="2 2"></path>
            <line x1="4" y1="19" x2="18" y2="10"></line>
            <polyline points="14 10 18 10 18 14"></polyline>
        </svg>'''
    
    return ''


