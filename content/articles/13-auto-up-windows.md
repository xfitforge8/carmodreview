---
title:
  en: "Why Only One Window Goes Up By Itself, and What You Can Do"
seo_title:
  en: "Why Only the Driver Window Has Auto-Up"
seo_desc:
  en: "One-touch up on the driver's window and nothing else is not a cost cut or a software lock. A federal standard explains it, and the fix is not a hack."
slug: auto-up-windows
category: Electrical
status: draft
published: 2026-11-06
last_updated: 2026-11-06
---

# Why Only One Window Goes Up By Itself, and What You Can Do

## EN

Almost every modern truck has one-touch **down** on all four windows and one-touch
**up** on the driver's only. Owners notice this, assume it is a restriction
somebody could unlock, and go looking for the setting.

There is no setting. Here is the actual reason, and the two separate situations
that people confuse with it.

### The rule that decides it

Federal Motor Vehicle Safety Standard 118, *Power-Operated Window, Partition, and
Roof Panel Systems*, lists the only circumstances in which a power window may
close: with the key in ON, START or ACCESSORY; by hand, unassisted; while an
exterior lock is continuously held; while a remote is continuously held within six
metres; in the interval after the key is turned off and before the front door
opens; or where the remaining gap is too small to pass a 4 mm rod.

Then the part that matters:

> <em>"A power-operated window, partition, or roof panel system that is capable of
> closing or of being closed under any circumstances other than those specified in
> S4 shall meet the requirements of S5.1, S5.2..."</em>

S5.1 requires that window to stop and reverse before it exerts 100 newtons on a
test rod — roughly ten kilograms of force. S5.2 requires it to reopen to at least
its starting position, or 125 mm further, or far enough to clear a 200 mm rod.

A one-touch-up window closes without anyone holding the switch. That is not one of
the S4 circumstances, so it falls under S5: it must be able to detect an obstacle
and reverse. The hardware that does that — a current-sensing motor module or a
pressure strip in the seal — is the reason one-touch-up costs more than one-touch
down. Downward travel has nothing in its way, so nothing has to be sensed.

That is the whole answer. It is not a subscription, not a software licence, and not
a line the dealer can move for you. A window without reversal hardware is not
permitted to close itself in the United States.

### What your manual procedure actually does

Search this and you will find a procedure, and it is real — it is in the owner's
manual under *Programming the Power Windows*:

1. Close all doors.
2. Turn the ignition on, or to ACC/ACCESSORY.
3. Partly open the window, close it, and keep holding the switch briefly after it
   has fully closed.
4. Open it, and keep holding briefly after it is fully open.

The manual introduces it with a condition that gets dropped when it is reposted:

> <em>"Programming may be necessary if the vehicle battery has been disconnected or
> discharged. If the window is unable to express-up, program each express-close
> window."</em>

*Each express-close window* — the windows that already have the feature. This
procedure does not add one-touch-up to a window that never had it. What it does is
restore the position memory after the body control module has lost power, so the
module knows where fully-closed and fully-open are. Without that reference it stops
one-touch operation rather than risk closing on something.

If your driver's window lost one-touch-up after a battery change, this is your fix
and it takes under a minute per window.

### So can it be added?

Physically, yes — a window module that intercepts the switch signal and drives the
window itself, with its own current sensing, is a real product and has existed for
decades. Whether it works on a given truck depends on whether the window switch
still carries a plain motor wire the module can interrupt. On vehicles where the
switch is a node on the CAN bus and the door module does the driving, there is no
such wire, and the module has nothing to tap.

That distinction — switch drives the motor directly, versus switch sends a message
— decides whether a retrofit is a two-hour job or not a job. It is worth knowing
which one you have before buying anything.

### What to check before you buy a module

**Whether your driver's window already has reversal.** If it does, the sensing
hardware exists on that door only. Check the other doors before assuming they can
mirror it.

**Whether the module lists your model year, not your model.** The switch-to-CAN
changeover happened at different times across different platforms, and it is the
single fact that determines whether a retrofit is possible.

**What happens with a person in the way.** A module that drives the window without
its own reversal function turns a one-touch switch into a window that can close on
an arm. Reversal is the feature, not the extra.

### What we could not verify

We have not installed a window module on any vehicle, and nothing here is a report
of one. The standard and the owner's-manual procedure are quoted from their own
text. Which specific model years retain a direct switch-to-motor circuit is a
per-platform question we have no source for, and the aftermarket products that
address it vary in whether they include current sensing at all.
