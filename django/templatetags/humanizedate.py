"""
This is a module to produce humanized dates adapting delta and resolution to the distance to the date from now.

NOTE! there is no translation for ["om", "sen", "sekunder"] even if ugettext() is used
author: Peter Lundberg, 2010
"""
from django.utils.translation import ugettext as _
from django import template
from django.template import defaultfilters
from datetime import datetime
from django.utils.timesince import timesince

register = template.Library()

@register.filter
def naturaldate(value, arg=None, datetime_now=None):
    """
    Provides a natural date for human readers as a filter
    for use in for instance timestamps of comments/blogs.
    
    # For example:
    >>> from datetime import datetime
    >>> naturaldate( datetime(2010, 03, 24, 15, 16), datetime_now=datetime(2010, 03, 24, 10, 11) )
    u'Today, 15:16'
    """
    datetime_now = datetime_now or datetime.now() 
    return _humanized_date(value, datetime_now)

@register.simple_tag
def naturaldate_span(value, arg=None, datetime_now=None):
    """
    Provides a natural date for human readers as a html snippet generator
    for use in for instance timestamps of comments/blogs.

    It wraps the date in a span with a css class (for javascript magic updating
    or styling) and a title (for hover effect with more details).
    
    # For example:
    >>> from datetime import datetime
    >>> naturaldate_span( datetime(2010, 03, 24, 14, 16), datetime_now=datetime(2010, 03, 24, 23, 15) )
    u'<span class="naturaldate" title="2010-03-24 14:16">Today, 14:16</span>'
    """
    datetime_now = datetime_now or datetime.now()     
    return '<span class="naturaldate" title="%s">%s</span>' % (
                        defaultfilters.date(value, arg="Y-m-d H:i"), 
                        _humanized_date(value, datetime_now) )

def _humanized_date(value, datetime_now):
    """
    Format the date with varying formats depending how it is relative to now.
                                    
    # Recent time is handled similar to timesince but with seconds
    >>> from datetime import datetime
    >>> _humanized_date( datetime(2010, 03, 24, 11, 15, 50), datetime(2010, 03, 24, 11, 15, 50) )
    u'2 sekunder sen'
    >>> _humanized_date( datetime(2010, 03, 24, 11, 15, 40), datetime(2010, 03, 24, 11, 15, 50) )
    u'10 sekunder sen'
    >>> _humanized_date( datetime(2010, 03, 24, 11, 14, 40), datetime(2010, 03, 24, 11, 15, 50) )
    u'1 minute sen'
    >>> _humanized_date( datetime(2010, 03, 24, 10, 15), datetime(2010, 03, 24, 11, 15) )
    u'1 hour sen'
    >>> _humanized_date( datetime(2010, 03, 24, 10, 05), datetime(2010, 03, 24, 11, 15) )
    u'1 hour, 10 minutes sen'

    # Time close in future is handled similar to timeuntil but with seconds
    >>> _humanized_date( datetime(2010, 03, 24, 11, 15, 50), datetime(2010, 03, 24, 11, 15, 40) )
    u'om 10 sekunder'
    >>> _humanized_date( datetime(2010, 03, 24, 11, 16, 50), datetime(2010, 03, 24, 11, 15, 40) )
    u'om 1 minute'
    >>> _humanized_date( datetime(2010, 03, 24, 16, 17, 50), datetime(2010, 03, 24, 11, 15, 40) )
    u'Today, 16:17'

    # Tomorrow is humanized if it is the next calender day (not just 24h)
    >>> _humanized_date( datetime(2010, 03, 25, 02, 16), datetime(2010, 03, 24, 20, 15) )
    u'Tomorrow, 2:16'
    >>> _humanized_date( datetime(2010, 03, 25, 02, 16), datetime(2010, 03, 24, 11, 15) )
    u'Tomorrow, 2:16'
    
    # Future dates only use a year if more than 6 months away
    >>> _humanized_date( datetime(2010, 05, 25, 11, 15), datetime(2010, 03, 24, 18, 15) )
    u'25 May'
    >>> _humanized_date( datetime(2020, 05, 25, 11, 15), datetime(2010, 03, 24, 18, 15) )
    u'25 May, 2020'

    # Today is humanized if it is the same calender day (not last 24h)
    >>> _humanized_date( datetime(2010, 03, 24, 11, 15), datetime(2010, 03, 24, 18, 15) )
    u'Today, 11:15'
    >>> _humanized_date( datetime(2010, 03, 23, 23, 15), datetime(2010, 03, 24, 18, 15) )
    u'Yesterday, 23:15'
    
    # yesterday is last calender day
    >>> _humanized_date( datetime(2010, 03, 23, 11, 15), datetime(2010, 03, 24, 11, 15) )
    u'Yesterday, 11:15'
    >>> _humanized_date( datetime(2010, 03, 23, 03, 15), datetime(2010, 03, 24, 23, 15) )
    u'Yesterday, 3:15'
    >>> _humanized_date( datetime(2010, 03, 22, 23, 45), datetime(2010, 03, 24, 23, 15) )
    u'22 March'

    # older dates are without a year until they are 6 months old
    >>> _humanized_date( datetime(2010, 02, 24, 16, 15), datetime(2010, 03, 24, 11, 15) )
    u'24 February'
    >>> _humanized_date( datetime(2009, 8, 24, 16, 15), datetime(2010, 03, 24, 11, 15) )
    u'24 August, 2009'
    >>> _humanized_date( datetime(2009, 02, 24, 16, 15), datetime(2010, 03, 24, 11, 15) )
    u'24 February, 2009'
    """
    try:
        # cut seconds and check it is a date
        value = datetime(value.year, value.month, value.day, value.hour, value.minute, value.second, 0)
    except:
        return value
    
    delta = datetime_now - value
    #assert False, "%s - %s delta is %d days and %d seconds" % (datetime_now, value, delta.days, delta.seconds)
    four_hours_in_seconds =  4*60*60
    six_months_in_days = 6*30
    if delta.days == 0 and delta.seconds >= 0:
        if delta.seconds < four_hours_in_seconds:
            if delta.seconds < 60:
                seconds = 2 if delta.seconds < 2 else delta.seconds #always plural
                return u'%d %s %s' % (seconds, _('sekunder'),  _('sen')) #todo change this to "seconds" and make translateable !
            else:
                return timesince(value, now=datetime_now) + ' ' + _('sen') #todo change this to "ago" and make translateable!
        elif value.day == datetime_now.day:
            return _(u'today').capitalize() + ', ' + defaultfilters.time(value.timetz(), arg="G:i")
        else:
            return _(u'yesterday').capitalize() + ', ' + defaultfilters.time(value.timetz(), arg="G:i")
    elif delta.days == 1:
        if value.toordinal() == datetime_now.toordinal()-1:
            return _(u'yesterday').capitalize() + ', ' + defaultfilters.time(value.timetz(), arg="G:i")
        else:
            return defaultfilters.date(value, arg="j F")
    elif abs(delta.days) > six_months_in_days:
        #use far date format
        return defaultfilters.date(value, arg="j F, Y")
    elif abs(delta.days) > 1:
        #use near date format
        return defaultfilters.date(value, arg="j F")
    elif delta.days == -1:
        #is near future (more than one day is handled with date near och fare date formats above)
        delta = value - datetime_now
        if delta.seconds < four_hours_in_seconds:
            if delta.seconds < 60:
                seconds = 2 if delta.seconds < 2 else delta.seconds #always plural
                return u'%s %d %s' % (_('om'), seconds, _('sekunder')) #todo change this to "seconds" and make translateable !
            else:
                return u'%s %s' % ( _('om'), timesince(datetime_now, now=value)) #todo change this to "in" and make translateable!
        elif value.day == datetime_now.day:
            return _(u'today').capitalize() + ', ' + defaultfilters.time(value.timetz(), arg="G:i")
        else:
            return _(u'tomorrow').capitalize() + ', ' + defaultfilters.time(value.timetz(), arg="G:i")
    else:
        #this should not happen, but lets be safe... assert False, "Logic error for delta.days=%d" % delta.days
        return defaultfilters.date(value, arg="Y-m-d H:i")

if __name__ == "__main__":
    import doctest
    doctest.testmod()

