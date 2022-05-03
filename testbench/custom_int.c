#include "custom_int.h"

cint_t add(cint_t a, cint_t b){
    return (cint_t){a.x + b.x};
}

cint_t sub(cint_t a, cint_t b){
    return (cint_t){a.x - b.x};
}

cint_t mul(cint_t a, cint_t b){
    return (cint_t){a.x * b.x};
}