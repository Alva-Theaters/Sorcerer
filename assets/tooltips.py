# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

'''
Minimizing Design Drag Coefficient (DDC) with Longer Tooltips

The Design Drag Coefficient (DDC) measures the time spent in a design process due to the 
Single-Point Delay of reading a tooltip (SPD) and consulting the manual (RTFM events). Contrary
to most UI design, Sorcerer intentionally uses longer tooltips liberally because the math
shows this actually reduces DDC. What the equation shows is that the time wasted by RTFM's
blows the time wasted by reading tooltips out of the water. So we want to reduce RTFM's at
all costs. One bad RTFM is the equivalent of reading a novella's worth of tooltips.

The general formula for DDC in this context is:

                N_actions * (T_SPD + (F_RTFM * T_RTFM))
    DDC = --------------------------------------------
                     N_actions * T_RTFM

Where:
    N_actions: The number of actions performed.
    T_SPD: Time to read a tooltip.
    F_RTFM: Frequency of RTFM events (as a fraction).
    T_RTFM: Time to read the manual (assumed to be 10 minutes = 600 seconds).

For short tooltips, where the delay is only 5% of 10 minutes for each RTFM event:

                 N_actions * (1 + (0.05 * T_RTFM))
    DDC_short = -----------------------------------
                    N_actions * T_RTFM

    DDC_short = (1000 * (1 + (0.05 * 600))) / (1000 * 600)
              = 0.050

For long tooltips, where the delay is 1% of 10 minutes per RTFM event:

                N_actions * (5 + (0.01 * T_RTFM))
    DDC_long = -----------------------------------
                   N_actions * T_RTFM

    DDC_long = (1000 * (5 + (0.01 * 600))) / (1000 * 600)
             = 0.0133
             
In summary:
- Short tooltips lead to a DDC_short of 0.050.
- Long tooltips lead to a DDC_long of 0.0133, meaning less time is wasted overall,
  via only a small decrease in RTFM frequency.

  In other words, we want to do everything we can to decrease RTFM's because that
  leads to disproportional gains in overall design efficiency.
'''


def find_tooltip(name):
    try:
        tooltip = english_tooltips[name.lower()]
    except:
        tooltip = ""
        print(f"Error: Could not find tooltip {name}. Returning empty string.")
    
    return format_tooltip(tooltip)


def format_tooltip(tooltip):
    if is_automatic_period():
        if tooltip.endswith("."): # In case dev forgot to remove period.
            tooltip = tooltip[:-1]
        return tooltip
    
    elif is_paragraph(tooltip):
        if not tooltip.endswith("."):
            tooltip = tooltip + "."
        return tooltip
    
    return tooltip


def is_automatic_period():
    return bpy.app.version < (4, 3) # Because Blender messed with stuff on 4.3.
    

def is_paragraph(text):
    word_threshold = 30
    sentence_threshold = 1 # Not 2 because a second sentence will not likely have a period.
    
    word_count = len(text.split())
    sentence_count = text.count('.') + text.count('!') + text.count('?')
    
    if word_count >= word_threshold or sentence_count >= sentence_threshold:
        return True
    else:
        return False
    

english_tooltips = {
    # Object Only
    "mute": "Mute this object's OSC output",
    "summon_movers": "Command line text to focus moving fixtures onto stage object",
    "erase": "Erase instead of add",
    "speaker_number": (
        '''Number of speaker in Qlab or on sound mixer. You're seeing this here because you selected a Speaker object, '''
        '''and speaker objects represent real, physical speakers in your theater for the purpose of spatial audio. To '''
        '''pan microphones left or right, you don't use an encoder, you just move the microphone or sound object closer '''
        '''to the left or right inside 3D view'''
    ),
    "sound_source": "Select either a sound strip in the sequencer or a microphone in Audio Patch",

    # Lighting Parameters
    "intensity": "Intensity value",
    "strobe": "Strobe value",
    "color": (
        "Color value. If your fixture is not an RGB fixture, but CMY, RGBA, or something like that, "
        "Sorcerer will automatically translate RGB to the correct color profile. The best way to tell "
        "Sorcerer which color profile is here on the object controller, to the right of this field. To make "
        "changes to many at a time, use the magic 'Profile to Apply' feature on the top left of this box, "
        "or the 'Apply Patch to Objects in Scene' button at the end of the group patch below this panel"
    ),
    "color_restore": (
        "Why are there 2 colors for this one? Because remotely making relative changes to color doesn't work well. "
        "Influencers use relative changes for everything but color for this reason. This second color picker picks "
        "the color the influencer will restore channels to after passing over"
    ),
    "pan": "Pan value",
    "tilt": "Tilt value",
    "zoom": "Zoom value",
    "iris": "Iris value",
    "edge": "Edge value",
    "diffusion": "Diffusion value",
    "gobo": "Gobo ID value",
    "speed": "Gobo rotation speed value",
    "prism": "Prism value",

    # Audio Parameters
    "volume": "Stage object microphone's intensity/value",

    # Common Header
    "manual_fixture_selection": (
        "Instead of the group selector to the left, simply type in what you wish to control here. Just type in the "
        "channels you want or don't want in plain English"
    ),
    "selected_group_enum": (
        '''Choose a fixtures to control. Use either the static Lighting Groups or the mesh's location relative to other '''
        '''meshes for a dynamic spatial selection instead (Dynamic)'''
    ),
    "selected_profile_enum": (
        '''Choose a fixture profile to apply to this fixture and any other selected fixtures. To copy settings directly '''
        '''from another light, select the lights you want to copy to, then select the light you wish to copy from, and '''
        '''then select the Dynamic option here'''
    ),
    "color_profile_enum": "Choose a color profile for the mesh based on the patch in the lighting console",
    "freezing_mode_enum": "Choose whether to render on all frames, every other frame, or every third frame",
    "solo": (
        "Mute all controllers but this one, and any others with solo also turned on. Clear all solos with the "
        "button on the Playback menu in the Timeline header"
    ),

    # Object Only
    "absolute": (
        "Enable absolute mode. In absolute mode, the object can animate the channels inside it while they are inside. " 
        "With this turned off, channels will only be changed by the influencer when the influencer comes and goes, not "
        "just because there is fcurve data. With this off, the influencer is in relative mode and can work on top of "
        "other effects"
    ),
    "strength": (
        "If you diminish the strength, it will act like a brush. If you keep this up all the way, it will act more like "
        "an object passing through the lights that resets them as it leaves"
    ),
    "sem": (
        '''If this is not zero, it  will behave like an "SEM" channel on ETC Eos. Use this to animate the translation '''
        '''of objects in Augment3D. This includes remote patching as well. To connect a 3D object in Augment3D to this '''
        '''channel, go to the right side tab in the A3D editor and drag the model over the SEM channel to link. Eos will '''
        '''not automatically put them on top of each other.'''
    ),

    # Mins and maxes
    "strobe_min": "Minimum value for strobe on the fixture itself",
    "strobe_max": "Maximum value for strobe on the fixture itself",
    "white_balance": (
        '''If the natural white is not truly white, make it be white here and then white on the Blender color '''
        '''picker will actually be white'''
    ),
    "pan_min": "Minimum value for pan on the fixture itself",
    "pan_max": "Maximum value for pan on the fixture itself",
    "tilt_min": "Minimum value for tilt on the fixture itself",
    "tilt_max": "Maximum value for tilt on the fixture itself",
    "zoom_min": "Minimum value for zoom on the fixture itself",
    "zoom_max": "Maximum value for zoom on the fixture itself",
    "speed_min": "Minimum value for gobo rotation speed on the fixture itself",
    "speed_max": "Maximum value for gobo rotation speed on the fixture itself",

    # Toggles
    "enable_audio": "Audio is enabled when checked",
    "enable_microphone": "Microphone volume is linked to Intensity when red",
    "enable_pan_tilt": "Pan/Tilt is enabled when checked",
    "enable_color": "Color is enabled when checked",
    "enable_diffusion": "Diffusion is enabled when checked",
    "enable_strobe": "Strobe is enabled when checked",
    "enable_zoom": "Zoom is enabled when checked",
    "enable_iris": "Iris is enabled when checked",
    "enable_edge": "Edge is enabled when checked",
    "enable_gobo": "Gobo is enabled when checked",
    "enable_prism": "Prism is enabled when checked",

    # Enable/Disable Arguments
    "simple_enable_disable_argument": "Add # for group ID",
    "gobo_argument": "Add # for group ID and $ for animation data",

    # Orb Executors
    "event_list": "This should be the number of the event list you have created on the console for this song",
    "cue_list": "This should be the number of the cue list you have created on the console for this song",
    "start_cue": (
        '''Specifies which cue will start (or enable) the timecode clock. Can't be the same as first cue in Blender '''
        '''sequence or that will create loop'''
    ),
    "end_cue": "Specifies which cue will stop (or disable) the timecode clock",
    "start_macro": "Universal macro used for various starting activities",
    "end_macro": "Universal macro used for various ending activities",
    "start_preset": "Universal preset used for various starting activities",
    "end_preset": "Universal preset used for various ending activities",

    # View3D Operators
    "alva_object.duplicate_object": "Duplicate and Slide",
    "duplicate_direction": "Direction of movement: 1 for positive, -1 for negative",
    "duplicate_quantity": "Number of duplicates to create"
}

spanish_tooltips = { # Translation provided by ChatGPT (GPT-4o) last on 11/30/2024.
    # Object Only
    "mute": "Silenciar la salida OSC de este objeto",
    "summon_movers": "Texto de línea de comando para enfocar luminarias móviles en el objeto del escenario",
    "erase": "Borrar en lugar de añadir",
    "speaker_number": (
        '''Número del altavoz en Qlab o en el mezclador de sonido. Estás viendo esto aquí porque seleccionaste un objeto Altavoz, '''
        '''y los objetos altavoz representan altavoces físicos reales en tu teatro para el propósito de audio espacial. Para '''
        '''mover micrófonos a la izquierda o derecha, no se usa un codificador; simplemente mueve el micrófono u objeto de sonido '''
        '''más cerca a la izquierda o derecha en la vista 3D'''
    ),
    "sound_source": "Selecciona una pista de sonido en el secuenciador o un micrófono en el Patch de Audio",

    # Lighting Parameters
    "intensity": "Valor de intensidad",
    "strobe": "Valor de estroboscopio",
    "color": (
        "Valor de color. Si tu luminaria no es RGB, sino CMY, RGBA o algo similar, "
        "Sorcerer traducirá automáticamente RGB al perfil de color correcto. La mejor manera de indicar "
        "a Sorcerer qué perfil de color usar es aquí en el controlador del objeto, a la derecha de este campo. "
        "Para realizar cambios masivos, usa la función mágica 'Perfil a Aplicar' en la esquina superior izquierda de este cuadro "
        "o el botón 'Aplicar Parche a Objetos en la Escena' al final del parche del grupo debajo de este panel."
    ),
    "color_restore": (
        "¿Por qué hay 2 colores para esto? Porque hacer cambios relativos remotamente al color no funciona bien. "
        "Los influenciadores usan cambios relativos para todo excepto para el color por esta razón. Este segundo selector de color "
        "elige el color al que el influenciador restaurará los canales después de pasar por encima."
    ),
    "pan": "Valor de paneo",
    "tilt": "Valor de inclinación",
    "zoom": "Valor de zoom",
    "iris": "Valor de iris",
    "edge": "Valor de borde",
    "diffusion": "Valor de difusión",
    "gobo": "Valor de ID de gobo",
    "speed": "Valor de velocidad de rotación del gobo",
    "prism": "Valor de prisma",

    # Audio Parameters
    "volume": "Intensidad/valor del micrófono del objeto del escenario",

    # Common Header
    "manual_fixture_selection": (
        "En lugar del selector de grupo a la izquierda, simplemente escribe lo que deseas controlar aquí. Escribe los "
        "canales que quieres o no quieres en lenguaje sencillo."
    ),
    "selected_group_enum": (
        '''Elige una luminaria para controlar. Usa ya sea los Grupos de Iluminación estáticos o la ubicación de la malla '''
        '''en relación con otras mallas para una selección espacial dinámica (Dinámico).'''
    ),
    "selected_profile_enum": (
        '''Elige un perfil de luminaria para aplicar a esta luminaria y a cualquier otra luminaria seleccionada. Para copiar '''
        '''configuraciones directamente de otra luz, selecciona las luces a las que quieres copiar, luego selecciona la luz '''
        '''de la que quieres copiar y luego selecciona la opción Dinámico aquí.'''
    ),
    "color_profile_enum": "Elige un perfil de color para la malla basado en el parche en la consola de iluminación",
    "freezing_mode_enum": "Elige si renderizar en todos los fotogramas, cada dos fotogramas o cada tres fotogramas",
    "solo": (
        "Silencia todos los controladores excepto este y cualquier otro con solo también activado. Borra todos los solos con el "
        "botón en el menú de Reproducción en el encabezado de la Línea de Tiempo."
    ),

    # Object Only
    "absolute": (
        "Habilita el modo absoluto. En modo absoluto, el objeto puede animar los canales dentro de él mientras están dentro. " 
        "Con esto desactivado, los canales solo serán cambiados por el influenciador cuando este entre y salga, no solo "
        "porque haya datos de curvas de animación. Con esto desactivado, el influenciador está en modo relativo y puede trabajar "
        "encima de otros efectos."
    ),
    "strength": (
        "Si disminuyes la fuerza, actuará como un pincel. Si mantienes esto al máximo, actuará más como un objeto que pasa a través "
        "de las luces y las reinicia al salir."
    ),
    "sem": (
        '''Si esto no es cero, se comportará como un canal "SEM" en ETC Eos. Úsalo para animar la traslación '''
        '''de objetos en Augment3D. Esto incluye parcheo remoto también. Para conectar un objeto 3D en Augment3D a este '''
        '''canal, ve a la pestaña derecha en el editor de A3D y arrastra el modelo sobre el canal SEM para vincularlo. '''
        '''Eos no los posicionará automáticamente juntos.'''
    ),

    # Mins and maxes
    "strobe_min": "Valor mínimo para el estroboscopio en la luminaria",
    "strobe_max": "Valor máximo para el estroboscopio en la luminaria",
    "white_balance": (
        '''Si el blanco natural no es realmente blanco, ajusta aquí para que el blanco en el selector de color de Blender '''
        '''sea realmente blanco.'''
    ),
    "pan_min": "Valor mínimo para el paneo en la luminaria",
    "pan_max": "Valor máximo para el paneo en la luminaria",
    "tilt_min": "Valor mínimo para la inclinación en la luminaria",
    "tilt_max": "Valor máximo para la inclinación en la luminaria",
    "zoom_min": "Valor mínimo para el zoom en la luminaria",
    "zoom_max": "Valor máximo para el zoom en la luminaria",
    "speed_min": "Valor mínimo para la velocidad de rotación del gobo en la luminaria",
    "speed_max": "Valor máximo para la velocidad de rotación del gobo en la luminaria",

    # Toggles
    "enable_audio": "El audio está habilitado cuando está marcado",
    "enable_microphone": "El volumen del micrófono está vinculado a la Intensidad cuando está en rojo",
    "enable_pan_tilt": "El paneo/inclinación está habilitado cuando está marcado",
    "enable_color": "El color está habilitado cuando está marcado",
    "enable_diffusion": "La difusión está habilitada cuando está marcada",
    "enable_strobe": "El estroboscopio está habilitado cuando está marcado",
    "enable_zoom": "El zoom está habilitado cuando está marcado",
    "enable_iris": "El iris está habilitado cuando está marcado",
    "enable_edge": "El borde está habilitado cuando está marcado",
    "enable_gobo": "El gobo está habilitado cuando está marcado",
    "enable_prism": "El prisma está habilitado cuando está marcado",

    # Enable/Disable Arguments
    "simple_enable_disable_argument": "Añade # para el ID del grupo",
    "gobo_argument": "Añade # para el ID del grupo y $ para los datos de animación",

    # Orb Executors
    "event_list": "Debe ser el número de la lista de eventos que has creado en la consola para esta canción",
    "cue_list": "Debe ser el número de la lista de cues que has creado en la consola para esta canción",
    "start_cue": (
        '''Especifica qué cue iniciará (o habilitará) el reloj de código de tiempo. No puede ser el mismo que el primer cue '''
        '''en la secuencia de Blender, ya que eso creará un bucle.'''
    ),
    "end_cue": "Especifica qué cue detendrá (o deshabilitará) el reloj de código de tiempo",
    "start_macro": "Macro universal usada para varias actividades iniciales",
    "end_macro": "Macro universal usada para varias actividades finales",
    "start_preset": "Preset universal usado para varias actividades iniciales",
    "end_preset": "Preset universal usado para varias actividades finales",

    # View3D Operators
    "alva_object.duplicate_object": "Duplicar y deslizar el objeto seleccionado",
    "duplicate_direction": "Dirección del movimiento: 1 para positivo, -1 para negativo",
    "duplicate_quantity": "Cantidad de duplicados a crear"

}