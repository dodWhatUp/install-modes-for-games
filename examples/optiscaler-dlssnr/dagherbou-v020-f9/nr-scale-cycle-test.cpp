#include "../OptiScaler/dlssnr/DlssNr_ScaleCycle.h"
#include <limits>

using DlssNr::NextWorkingScale;
static_assert(NextWorkingScale(1.0f) == 0.75f);
static_assert(NextWorkingScale(0.75f) == 0.67f);
static_assert(NextWorkingScale(0.67f) == 0.50f);
static_assert(NextWorkingScale(0.50f) == 1.0f);
static_assert(NextWorkingScale(0.750001f) == 0.67f);
static_assert(NextWorkingScale(0.80f) == 0.75f);
static_assert(NextWorkingScale(0.65f) == 0.50f);
static_assert(NextWorkingScale(2.0f) == 1.0f);
static_assert(NextWorkingScale(0.25f) == 1.0f);
static_assert(NextWorkingScale(-1.0f) == 1.0f);
static_assert(NextWorkingScale(std::numeric_limits<float>::quiet_NaN()) == 1.0f);
int main() { return 0; }
