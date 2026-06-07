import random
from collections import Counter

from sqlalchemy import Select
from sqlalchemy.orm import Session

from models import Category, Runner


def assign_times(db, cat_name, cat_zero, baseint_delta, method):
    with Session(db) as sess:
        order = method(sess, cat_name)

        last = cat_zero
        for runner in order:
            runner.startlist_time = last
            last += baseint_delta

        sess.commit()


def completely_random(sess, cat_name):
    cat = sess.scalars(
        Select(Category).where(Category.name == cat_name)
    ).first()
    runners = list(
        sess.scalars(Select(Runner).where(Runner.category == cat)).all()
    )

    random.shuffle(runners)

    return runners


def ardfevent_draw(sess, cat_name):
    cat = sess.scalars(
        Select(Category).where(Category.name == cat_name)
    ).first()

    if not cat:
        return []

    runners = list(
        sess.scalars(Select(Runner).where(Runner.category == cat)).all()
    )

    random.shuffle(runners)

    def solve(current_list, remaining_items):
        if not remaining_items:
            return current_list

        last_club = current_list[-1].club if current_list else None

        candidates = [r for r in remaining_items if r.club != last_club]

        if not candidates:
            return None

        counts = Counter(r.club for r in remaining_items)
        total_remaining = len(remaining_items)

        must_pick_clubs = [
            club for club, count in counts.items()
            if count > (total_remaining // 2)
        ]

        if must_pick_clubs:
            pick_pool = [r for r in candidates if r.club in must_pick_clubs]
            if not pick_pool:
                return None
        else:
            pick_pool = candidates
            random.shuffle(pick_pool)

        for runner in pick_pool:
            new_remaining = [r for r in remaining_items if r != runner]
            result = solve(current_list + [runner], new_remaining)
            if result is not None:
                return result

        return None

    final_result = solve([], runners)

    if final_result is None:
        final_result = []
        groups = {}
        for obj in runners:
            groups.setdefault(obj.club, []).append(obj)
        for club in groups:
            random.shuffle(groups[club])

        while len(final_result) < len(runners):
            last_club = final_result[-1].club if final_result else None
            available_clubs = [c for c in groups if groups[c]]

            max_f = max(len(groups[c]) for c in available_clubs)
            cands = [c for c in available_clubs if len(groups[c]) == max_f and c != last_club]
            if not cands:
                cands = [c for c in available_clubs if c != last_club]

            choice = random.choice(cands) if cands else available_clubs[0]
            final_result.append(groups[choice].pop())

    return final_result
