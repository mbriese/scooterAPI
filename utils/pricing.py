"""
Pricing Utility Module
Calculates rental costs based on duration and pricing tiers
"""
import logging
from datetime import datetime, timedelta
from config import (
    RENTAL_UNLOCK_FEE,
    RENTAL_HOURLY_RATE,
    RENTAL_MIN_CHARGE_MINUTES,
    RENTAL_DAILY_RATE,
    RENTAL_MULTIDAY_RATES,
    RENTAL_WEEKLY_RATE,
    RENTAL_MONTHLY_RATE,
    RENTAL_GRACE_PERIOD_MINUTES,
    RENTAL_MAX_DURATION_DAYS
)

logger = logging.getLogger(__name__)


def calculate_rental_cost(start_time, end_time=None):
    """
    Calculate the rental cost based on duration.
    
    Pricing tiers (best rate applied automatically):
    - Grace period: Free (under 2 minutes)
    - Hourly: $3.50/hour (minimum 15 min increments)
    - Daily: $25.00/day (better than 7+ hours)
    - Multi-day: Discounted rates for 2-6 days
    - Weekly: $99.00/week (best for 7+ days up to ~12 days)
    - Monthly: $299.00/month (best for 12+ days)
    
    Returns dict with cost breakdown.
    """
    if end_time is None:
        end_time = datetime.now()
    
    # Handle string timestamps
    if isinstance(start_time, str):
        start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    if isinstance(end_time, str):
        end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    
    # Calculate duration
    duration = end_time - start_time
    total_minutes = duration.total_seconds() / 60
    total_hours = total_minutes / 60
    total_days = total_hours / 24
    
    logger.info(f"Calculating rental cost: {total_minutes:.1f} minutes ({total_hours:.2f} hours, {total_days:.2f} days)")
    
    # Grace period - no charge
    if total_minutes <= RENTAL_GRACE_PERIOD_MINUTES:
        return {
            'duration_minutes': round(total_minutes, 1),
            'duration_hours': round(total_hours, 2),
            'duration_days': round(total_days, 2),
            'pricing_tier': 'grace_period',
            'unlock_fee': 0.00,
            'rental_fee': 0.00,
            'total_cost': 0.00,
            'description': 'Grace period - no charge'
        }
    
    # Determine best pricing tier
    pricing_tier, rental_fee, description = _get_best_rate(total_minutes, total_hours, total_days)
    
    # Add unlock fee
    total_cost = RENTAL_UNLOCK_FEE + rental_fee
    
    return {
        'duration_minutes': round(total_minutes, 1),
        'duration_hours': round(total_hours, 2),
        'duration_days': round(total_days, 2),
        'pricing_tier': pricing_tier,
        'unlock_fee': RENTAL_UNLOCK_FEE,
        'rental_fee': round(rental_fee, 2),
        'total_cost': round(total_cost, 2),
        'description': description
    }


def _get_best_rate(total_minutes, total_hours, total_days):
    """
    Determine the best (cheapest) rate for the given duration.
    Returns tuple of (tier_name, rental_fee, description).
    """
    options = []
    
    # Hourly rate calculation
    billable_minutes = max(RENTAL_MIN_CHARGE_MINUTES, total_minutes)
    # Round up to next 15-minute increment
    billable_increments = -(-int(billable_minutes) // RENTAL_MIN_CHARGE_MINUTES)
    hourly_cost = (billable_increments * RENTAL_MIN_CHARGE_MINUTES / 60) * RENTAL_HOURLY_RATE
    options.append(('hourly', hourly_cost, f'{billable_increments * RENTAL_MIN_CHARGE_MINUTES} min @ ${RENTAL_HOURLY_RATE}/hr'))
    
    # Daily rate (if more than ~7 hours, daily is better)
    if total_hours >= 1:
        days_needed = max(1, int(-(-total_days // 1)))  # Ceiling division
        if days_needed == 1:
            daily_cost = RENTAL_DAILY_RATE
            options.append(('daily', daily_cost, f'1 day @ ${RENTAL_DAILY_RATE}'))
        elif days_needed in RENTAL_MULTIDAY_RATES:
            multiday_cost = RENTAL_MULTIDAY_RATES[days_needed]
            options.append(('multi_day', multiday_cost, f'{days_needed} days @ ${multiday_cost} (discounted)'))
        elif days_needed < 7:
            # Calculate cost for days not in the rate table
            multiday_cost = RENTAL_DAILY_RATE * days_needed * 0.85  # 15% discount
            options.append(('multi_day', multiday_cost, f'{days_needed} days @ ${multiday_cost:.2f} (15% off)'))
    
    # Weekly rate (if 7+ days)
    if total_days >= 5:
        weeks_needed = max(1, int(-(-total_days // 7)))
        remaining_days = total_days - (weeks_needed - 1) * 7
        
        if weeks_needed == 1:
            weekly_cost = RENTAL_WEEKLY_RATE
            options.append(('weekly', weekly_cost, f'1 week @ ${RENTAL_WEEKLY_RATE}'))
        else:
            weekly_cost = (weeks_needed - 1) * RENTAL_WEEKLY_RATE + (RENTAL_WEEKLY_RATE if remaining_days > 0 else 0)
            options.append(('weekly', weekly_cost, f'{weeks_needed} weeks @ ${RENTAL_WEEKLY_RATE}/wk'))
    
    # Monthly rate (if 12+ days, monthly might be better)
    if total_days >= 12:
        months_needed = max(1, int(-(-total_days // 30)))
        monthly_cost = months_needed * RENTAL_MONTHLY_RATE
        options.append(('monthly', monthly_cost, f'{months_needed} month(s) @ ${RENTAL_MONTHLY_RATE}/mo'))
    
    # Find the cheapest option
    best_option = min(options, key=lambda x: x[1])
    logger.info(f"Best rate for {total_hours:.2f}h: {best_option[0]} = ${best_option[1]:.2f}")
    
    return best_option


def get_pricing_info():
    """
    Get pricing information for display to users.
    """
    return {
        'unlock_fee': RENTAL_UNLOCK_FEE,
        'hourly_rate': RENTAL_HOURLY_RATE,
        'min_charge_minutes': RENTAL_MIN_CHARGE_MINUTES,
        'daily_rate': RENTAL_DAILY_RATE,
        'multiday_rates': RENTAL_MULTIDAY_RATES,
        'weekly_rate': RENTAL_WEEKLY_RATE,
        'monthly_rate': RENTAL_MONTHLY_RATE,
        'grace_period_minutes': RENTAL_GRACE_PERIOD_MINUTES,
        'max_duration_days': RENTAL_MAX_DURATION_DAYS
    }


def estimate_cost(hours=None, days=None):
    """
    Estimate rental cost for a given duration.
    Useful for showing users expected costs before renting.
    """
    if days:
        total_minutes = days * 24 * 60
    elif hours:
        total_minutes = hours * 60
    else:
        return None
    
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=total_minutes)
    
    return calculate_rental_cost(start_time, end_time)


def format_duration(minutes):
    """Format duration in human-readable format."""
    if minutes < 60:
        return f"{int(minutes)} min"
    elif minutes < 1440:  # Less than a day
        hours = minutes / 60
        return f"{hours:.1f} hours"
    else:
        days = minutes / 1440
        if days < 7:
            return f"{days:.1f} days"
        elif days < 30:
            weeks = days / 7
            return f"{weeks:.1f} weeks"
        else:
            months = days / 30
            return f"{months:.1f} months"

