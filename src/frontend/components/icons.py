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
    
    return ''
