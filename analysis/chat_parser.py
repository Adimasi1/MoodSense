"""
WhatsApp Chat Parser

This program analyze the export file from WhatsApp (.txt) and convert the content to a 
Ptyhon structure.

Supported formats:
- Export italiano: "11/10/2024, 14:23 - Nome Utente: Messaggio"
- Export inglese: "10/11/2024, 2:23 PM - User Name: Message"
- Mutiple rows message
- Media (photos, videos, GIF, stickers, documents)
- Emoji and special characters

Output: List of dictionaries with timestamp, user, message, type of media
"""

import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple


# ============================================================================
# PATTERN CONFIGURATION
# ============================================================================

# Main pattern to recognize a new WhatsApp message line
# Captures: date, time, username, message
# Supported formats:
#   - "11/10/2024, 14:23 - Mario Rossi: Ciao"
#   - "10/11/2024, 2:23 PM - John Doe: Hello"
WHATSAPP_LINE_PATTERN = re.compile(
    r'^(\d{1,2}/\d{1,2}/\d{4}),\s(\d{1,2}:\d{2}(?:\s?[AP]M)?)\s-\s(.+?):\s(.*)$',
    re.MULTILINE
) #re.come creates a reusable regular expression object

# Pattern to recognize system messages (to optionally filter out)
# E.g.: "Mario changed the group image"
SYSTEM_MESSAGE_PATTERNS = [
    r'ha cambiato l\'immagine del gruppo',
    r'ha cambiato la descrizione del gruppo',
    r'ha aggiunto',
    r'ha lasciato',
    r'changed the group',
    r'added',
    r'left',
    r'created group',
    r'Messages and calls are end-to-end encrypted',
    r'I messaggi e le chiamate sono crittografati end-to-end'
]

# Pattern to recognize media
MEDIA_PATTERNS = {
    'photo': [r'<Media omessi>', r'<Media omitted>', r'image omitted', r'IMG-'],
    'video': [r'video omitted', r'VID-', r'\.mp4'],
    'gif': [r'GIF omitted', r'\.gif'],
    'sticker': [r'sticker omitted', r'STK-'],
    'audio': [r'audio omitted', r'PTT-', r'AUD-'],
    'document': [r'document omitted', r'\.pdf', r'\.docx']
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_timestamp(date_str: str, time_str: str) -> Optional[datetime]:
    """
    Converts date/time strings to datetime object.
    
    Supported formats:
    - Italian: "11/10/2024", "14:23"
    - English 12h: "10/11/2024", "2:23 PM"
    - English 24h: "10/11/2024", "14:23"
    
    Args:
        date_str: date string in "dd/mm/yyyy" or "mm/dd/yyyy" format
        time_str: time string in "HH:MM" or "H:MM AM/PM" format
    
    Returns:
        datetime object or None if parsing fails
    """
    # Try Italian 24h format (most common in EU)
    try:
        dt_str = f"{date_str} {time_str}"
        return datetime.strptime(dt_str, "%d/%m/%Y %H:%M")

    except ValueError:
        pass
    
    # Try English 12h format with AM/PM
    try:
        dt_str = f"{date_str} {time_str}"
        return datetime.strptime(dt_str, "%m/%d/%Y %I:%M %p")
    except ValueError:
        pass
    
    # Try English 24h format
    try:
        dt_str = f"{date_str} {time_str}"
        return datetime.strptime(dt_str, "%m/%d/%Y %H:%M")
    except ValueError:
        pass
    
    # Fallback: try reversing day/month
    try:
        dt_str = f"{date_str} {time_str.replace(' ', '')}"
        return datetime.strptime(dt_str, "%d/%m/%Y %H:%M")
    except ValueError:
        return None

def get_hour_category(timestamp: datetime) -> str:
    if not timestamp:
        return ""

    # HOURS intervals: [08-10) [10, 12)
    HOURS = ["00-02", "02-04", "04-06", "06-08", "08-10", "10-12",
              "12-14", "14-16", "16-18", "18-20", "20-22", "22-24"]
    
    category_index = timestamp.hour // 2
    return HOURS[category_index]

def weekday_from_int_to_string(weekday: int) -> str:
    if weekday == 0:
        return "Monday"
    elif weekday == 1:
        return "Tuesday"
    elif weekday == 2:
        return "Wednesday"
    elif weekday == 3:
        return "Thursday"
    elif weekday == 4:
        return "Friday"
    elif weekday == 5:
        return "Saturday"
    elif weekday == 6:
        return "Sunday"
    else:
        return "Invalid day number"

def detect_media_type(message_text: str) -> Tuple[bool, Optional[str]]:
    """
    Detects if the message contains media and identifies the type.
    
    Args:
        message_text: message text
    
    Returns:
        (is_media: bool, media_type: str | None)
        
    Examples:
        >>> detect_media_type("<Media omessi>")
        (True, "photo")
        >>> detect_media_type("video omitted")
        (True, "video")
        >>> detect_media_type("Ciao come stai?")
        (False, None)
    """
    message_lower = message_text.lower()
    
    for media_type, patterns in MEDIA_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True, media_type
    
    return False, None


def is_system_message(message_text: str) -> bool:
    """
    Checks if the message is a WhatsApp system message.
    
    Args:
        message_text: message text
    
    Returns:
        True if it's a system message
        
    Examples:
        >>> is_system_message("Mario ha cambiato l'immagine del gruppo")
        True
        >>> is_system_message("Ciao ragazzi!")
        False
    """
    for pattern in SYSTEM_MESSAGE_PATTERNS:
        if re.search(pattern, message_text, re.IGNORECASE):
            return True
    return False


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def parse_whatsapp_export(
    file_content: str,
    skip_system_messages: bool = True,
    preserve_media_messages: bool = True
) -> List[Dict]:
    """
    Parses WhatsApp export content and returns a list of structured messages.
    
    Args:
        file_content: string with the entire content of the exported .txt file
        skip_system_messages: if True, excludes system messages (default: True)
        preserve_media_messages: if True, includes media messages (default: True)
    
    Returns:
        List of dictionaries, one per message, with keys:
        - timestamp (datetime): message date/time
        - user (str): username who sent the message
        - message (str): message text (can be empty if media only)
        - is_media (bool): True if the message contains media
        - media_type (str | None): media type ("photo", "video", "gif", etc.)
        - is_system (bool): True if it's a WhatsApp system message
    
    Example:
        >>> content = '''11/10/2024, 14:23 - Mario: Ciao!
        ... 11/10/2024, 14:25 - Luca: <Media omessi>
        ... 11/10/2024, 14:26 - Mario: Come stai?'''
        >>> messages = parse_whatsapp_export(content)
        >>> len(messages)
        3
        >>> messages[1]['is_media']
        True
    """
    messages = []
    lines = file_content.split('\n')
    
    current_message = None  # Tracks current message to handle multiline
    
    for line in lines:
        line = line.strip()
        if not line:  # Skip empty lines
            continue
        
        # Try to match with WhatsApp pattern (new message line)
        match = WHATSAPP_LINE_PATTERN.match(line)
        
        if match:
            # It's a new message line: save the previous one if it exists
            if current_message is not None:
                messages.append(current_message)
            
            # Extract components from match
            date_str, time_str, user_name, message_text = match.groups()
            
            # Parse timestamp
            timestamp = parse_timestamp(date_str, time_str)
            if timestamp is None:
                # If parsing fails, skip message (may be unsupported format)
                continue

            # Hour category
            hour_category = get_hour_category(timestamp)     

            # weekday
            weekday = weekday_from_int_to_string(timestamp.weekday())

            # number of characthers
            number_of_characthers = len(message_text)

            # Detect media
            is_media, media_type = detect_media_type(message_text)
            
            # Detect system messages
            is_sys = is_system_message(message_text)
            
            # Create message structure
            current_message = {
                'timestamp': timestamp,
                'weekday': weekday,
                'hour_category': hour_category,
                'user': user_name.strip(),
                'message': message_text.strip(),
                'message_length': number_of_characthers,
                'is_media': is_media,
                'media_type': media_type,
                'is_system': is_sys
            }
        
        else:
            # Not a new line: it's a multiline continuation of the previous message
            if current_message is not None:
                # Append to the 'message' key of the current message
                current_message['message'] += '\n' + line
    
    # Add the last message if it exists
    if current_message is not None:
        messages.append(current_message)
    
    # Optional filtering
    filtered_messages = []
    for msg in messages:
        # Skip system messages if requested
        if skip_system_messages and msg['is_system']:
            continue
        
        # Skip media messages if requested
        if not preserve_media_messages and msg['is_media']:
            continue
        
        filtered_messages.append(msg)
    
    return filtered_messages


# ============================================================================
# UTILITY FUNCTIONS FOR ANALYSIS
# ============================================================================

def get_chat_metadata(messages: List[Dict]) -> Dict:
    """
    Extracts general metadata from parsed chat.
    
    Args:
        messages: message list from parse_whatsapp_export()
    
    Returns:
        Dictionary with metadata:
        - total_messages: total number of messages
        - num_users: number of unique users
        - users: list of user names
        - start_date: timestamp of first message
        - end_date: timestamp of last message
        - total_media: number of messages with media
        - media_by_type: media count by type
    """
    if not messages:
        return {
            'total_messages': 0,
            'num_users': 0,
            'users': [],
            'start_date': None,
            'end_date': None,
            'total_media': 0,
            'media_by_type': {}
        }
    
    users = list(set(msg['user'] for msg in messages))
    media_messages = [msg for msg in messages if msg['is_media']]

    #count by user and count media type
    media_by_user = {}
    media_by_type = {}
    for msg in media_messages:
        user = msg['user'] or 'unknown'
        media_by_user[user] = media_by_user.get(user, 0) + 1

        mtype = msg['media_type'] or 'unknown'
        media_by_type[mtype] = media_by_type.get(mtype, 0) + 1

    return {
        'total_messages': len(messages),
        'num_users': len(users),
        'users': users,
        'users': sorted(users),
        'start_date': messages[0]['timestamp'],
        'end_date': messages[-1]['timestamp'],
        'total_media': len(media_messages),
        'media_by_user': media_by_user,
        'media_by_type': media_by_type
    }


def filter_messages_by_user(messages: List[Dict], user_name: str) -> List[Dict]:
    """
    Filters messages from a single user.
    
    Args:
        messages: message list
        user_name: exact user name
    
    Returns:
        List of messages only from that user
    """
    return [msg for msg in messages if msg['user'] == user_name]


def filter_messages_by_date_range(
    messages: List[Dict],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Dict]:
    """
    Filters messages within a time range.
    
    Args:
        messages: message list
        start_date: range start (inclusive). None = no lower limit
        end_date: range end (inclusive). None = no upper limit
    
    Returns:
        List of messages within the range
    """
    filtered = messages
    
    if start_date:
        filtered = [msg for msg in filtered if msg['timestamp'] >= start_date]
    
    if end_date:
        filtered = [msg for msg in filtered if msg['timestamp'] <= end_date]
    
    return filtered
