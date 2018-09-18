These are the release notes for SymPy 1.2.

SymPy 1.2 was released on Jul 9, 2018.

This version of SymPy has been tested on Python 2.7, 3.4, 3.5, 3.6, 3.7 and
PyPy. See our [Python version support
policy](https://github.com/sympy/sympy/wiki/Python-version-support-policy) for
more information on when we plan to drop support for older Python versions.

Install SymPy with

    pip install -U sympy

or if you use Anaconda

    conda install sympy

## Highlights

There are many changes in 1.2 (see below). Some of the highlights are

* Python 3.3 is no longer supported. If you require Python 3.3 support, use
  SymPy 1.1.1. See our
  [policy](https://github.com/sympy/sympy/wiki/Python-version-support-policy)
  on dropping support for major Python versions.

* Experimental LaTeX parsing with `sympy.parsing.latex.parse_latex()` has been
  added, based on the `latex2sympy` project. This requires
  `antlr-python-runtime` to be installed.
  [#13706](https://github.com/sympy/sympy/pull/13706)

* The vector module has been improved to support orthogonal curvilinear
  coordinate systems ([Szymon Mieszczak's GSoC
  project](https://github.com/sympy/sympy/wiki/Szymon-Mieszczak,-GSoC-2017-Report,-Implementation-of-multiple-types-of-coordinate-systems-for-vectors))

* New module `sympy.integrals.intpoly` for integrating uni/bivariate polynomials
  over 2-polytopes. ([Arif Ahmed's GSoC
  project](https://github.com/sympy/sympy/wiki/GSoC-2017-Report-Arif-Ahmed-:-Integration-over-Polytopes))

* Improvements to the code generation module. ([Björn Dahlgren's GSoC
  project](https://github.com/sympy/sympy/wiki/GSoC-2017-Report-Bj%C3%B6rn-Dahlgren:-Improved-code-generation-facilities))

* Improvements to the group theory module. See below for more information.
  ([Valeriia Gladkova's GSoC
  project](https://github.com/sympy/sympy/wiki/GSoC-2017-Report-Valeriia-Gladkova:-Group-Theory))

* New module `sympy.discrete` for operating on discrete sequences. ([Sidhant Nagpal's GSoC
  project](https://github.com/sidhantnagpal/gsoc/wiki/GSoC-2018-Application-Sidhant-Nagpal:-Transforms,-Convolution-&-Linear-Recurrence-Evaluation))

Other GSoC projects, [Abdullah Javed
Nesar](https://github.com/sympy/sympy/wiki/GSoC-2017-Report-Abdullah-Javed-Nesar:-Rule-based-Integrator),
[Arif
Ahmed](https://github.com/sympy/sympy/wiki/GSoC-2017-Report-Arif-Ahmed-:-Integration-over-Polytopes),
and [Gaurav Dhingra](https://github.com/gxyd/GSoC-2017-Report) are work in
progress improvements to the `integrate` module (particularly, the new `rubi`
submodule and the `risch` submodule), which are not yet visible to user-facing
code.

## Backwards compatibility breaks and deprecations

* Units: the arguments `dimension` and `scale_factor` in `Quantity` have been
  deprecated (see [#14319](https://github.com/sympy/sympy/issues/14319)).

* Units: Dimensional dependencies are now part of DimensionSystem. All related
  methods inside Dimension have been deprecated in favor of the methods in
  DimensionSystem (see [#13336](https://github.com/sympy/sympy/issues/13336)).

* `Matrix.dot` now only works for row and column matrices. Use `*` or `@` to
  do matrix multiplication. (see
  [#13815](https://github.com/sympy/sympy/issues/13815)).

* The `k` argument for `line3D.equation()` is deprecated (see
  [#13742](https://github.com/sympy/sympy/issues/13742)).

* `lambdify` no longer automatically wraps arguments with `np.array`, which
  improves the performance of calls to lambdified functions. Array wrapping is
  necessary if the input involves an operation that would raise an exception
  on scalar input, such `lambdify(x, 1/x)(0)`, but these cases are relatively
  rare, and wrapping can always be done by the user if necessary.
  [#14823](https://github.com/sympy/sympy/pull/14823)

## Changes

* algebras
  * add new algebras submodule
  * add Quaternion class [#13285](https://github.com/sympy/sympy/pull/13285)

* calculus
  * periodicity: added support for modulo operation
    [#13226](https://github.com/sympy/sympy/pull/13226)
  * fixed continuous_domain to remove singularities.
    [#13335](https://github.com/sympy/sympy/pull/13335)
  * Finite Set domains for `function_range`
    [#13479](https://github.com/sympy/sympy/pull/13479)
  * Fix `function_range` for periodic functions
    [#13512](https://github.com/sympy/sympy/pull/13512)

* combinatorics
  * correct gray_to_bin and bin_to_gray
    [#14468](https://github.com/sympy/sympy/pull/14468)
  * improve the comparison test for convergence
    [#14509](https://github.com/sympy/sympy/pull/14509)

* concrete
  * Improve summation of geometric series
    [#13991](https://github.com/sympy/sympy/pull/13991)
  * add the ratio test to Sum.is_convergent
    [#14158](https://github.com/sympy/sympy/pull/14158)
  * add the limit comparison test for is_convergent
    [#14401](https://github.com/sympy/sympy/pull/14401)
  * add bounded times summation convergence test
    [#14464](https://github.com/sympy/sympy/pull/14464)
  * add factoring to compute certain sums with negative exponents
    [#14641](https://github.com/sympy/sympy/pull/14641)

* core
  * Derivatives by a variable a symbolic number of times, like `diff(f(x), (x,
    n))` to represent `d^nf/dx^n`, where `n` can be symbolic.
    [#13751](https://github.com/sympy/sympy/pull/13751)
    [#13892](https://github.com/sympy/sympy/pull/13892)
  * various improvements to `Piecewise` and `piecewise_fold`.
    [#12951](https://github.com/sympy/sympy/pull/12951),
    [#12920](https://github.com/sympy/sympy/pull/12920),
    [#13074](https://github.com/sympy/sympy/pull/13074),
    [#13282](https://github.com/sympy/sympy/pull/13282),
    [#13309](https://github.com/sympy/sympy/pull/13309),
    [#13204](https://github.com/sympy/sympy/pull/13204),
    [#12587](https://github.com/sympy/sympy/pull/12587),
    [#14071](https://github.com/sympy/sympy/pull/14071),
    [#14682](https://github.com/sympy/sympy/pull/14682)
  * Make Pow.subs not use fractional powers for noncommutative objects
    [#13018](https://github.com/sympy/sympy/pull/13018)
  * nullary undefined functions (like `f = Function('f'); f()`) are now
    allowed [#12977](https://github.com/sympy/sympy/pull/12977)
  * add a global option and context manager to disable automatic distribution
    (`2*(x + y)` -> `2*x + 2*y`)
    [#12440](https://github.com/sympy/sympy/pull/12440)
  * make Mul.flatten aware of MatrixExpr
    [#13279](https://github.com/sympy/sympy/pull/13279)
  * Fix `__rfloordiv__` not being reversed
    [#13368](https://github.com/sympy/sympy/pull/13368)
  * `Expr` now supports the 3-argument version of the builtin `pow`
    [#13364](https://github.com/sympy/sympy/pull/13364)
  * Allow undefined functions to be defined with assumptions (like
    `Function('f', real=True)`).
    [#12945](https://github.com/sympy/sympy/pull/12945)
  * Allow Floats to be created from NumPy floats
    [#13426](https://github.com/sympy/sympy/pull/13426)
  * Fix some incorrect comparisons between numbers
    [#13429](https://github.com/sympy/sympy/pull/13429)
  * removed x**1.0 == x hack from the core (they are now unequal, remember
    that `==` in SymPy means symbolic, not mathematical equality)
    [#13518](https://github.com/sympy/sympy/pull/13518)
  * Subs substitution now supports derivative by indexed objects in various
    cases [#13452](https://github.com/sympy/sympy/pull/13452)
  * Add more simplifications for Mod
    [#13581](https://github.com/sympy/sympy/pull/13581)
  * make `f(1).is_number` give False, where `f = Function('f')`
    [#13619](https://github.com/sympy/sympy/pull/13619)
  * allow differentiating with respect to tuples, returning an Array type
    [#13655](https://github.com/sympy/sympy/pull/13655)
  * correct sympify for numpy arrays of size 1
    [#13926](https://github.com/sympy/sympy/pull/13926)
  * Do not over-simplify rational powers of negative integers
    [#13895](https://github.com/sympy/sympy/pull/13895)
  * Fix the negative rational powers of negative integers and rationals
    [#14024](https://github.com/sympy/sympy/pull/14024)
  * improve the performance of modular exponentiation for very large powers
    [#14249](https://github.com/sympy/sympy/pull/14249)
  * improve mod_inverse for negative numbers
    [#14333](https://github.com/sympy/sympy/pull/14333)
  * prevent infinite recursion in as_real_imag
    [#14404](https://github.com/sympy/sympy/pull/14404)
  * remove automatic distribution of infinite factors
    [#14383](https://github.com/sympy/sympy/pull/14383)
  * fix floor and ceiling of infinite quantities
    [#14328](https://github.com/sympy/sympy/pull/14328)
  * fix evaluation of negative terms with sympify(evaluate=False)
    [#11095](https://github.com/sympy/sympy/issues/11095)
  * SymPy numeric expressions now work with `math.trunc`
    [#14451](https://github.com/sympy/sympy/pull/14451)
  * fix `Mod(x**2, x)` giving 0 (it is not 0 if `x` is fractional)
    [#13177](https://github.com/sympy/sympy/pull/13177)
  * fix evalf with subs giving incorrect results with `floor`
    [#13361](https://github.com/sympy/sympy/pull/13361)
  * prevent substitutions in Derivative in cases where it changes the
    mathematical meaning of the expression
    [#13803](https://github.com/sympy/sympy/pull/13803)
  * allow complex powers to be rewritten as exp
    [#14712](https://github.com/sympy/sympy/pull/14712)

* codegen
  * Improvements to the code generation module. ([Björn Dahlgren's GSoC
  project](https://github.com/sympy/sympy/wiki/GSoC-2017-Report-Bj%C3%B6rn-Dahlgren:-Improved-code-generation-facilities)), including:
    * many additions to the sympy.codegen.ast module
    * new sympy.codegen rewriting module with codegen related expression
      optimizations
    * new sympy.codegen.algorithms module with code generatable algorithms using
      codegen.ast
    * new sympy.codegen.approximations module with code generatable approximations
  * add a code printer for GLSL (`glsl_code`)
    [#12713](https://github.com/sympy/sympy/pull/12713)
  * add support for tensorflow 1.0+
    [#13413](https://github.com/sympy/sympy/pull/13413)
  * added printer flag so that printer can be passed to codegen()
    [#13587](https://github.com/sympy/sympy/pull/13587)
  * Add support for fmod in ccode
    [#13692](https://github.com/sympy/sympy/pull/13692)
  * add more functions to rcode
    [#13840](https://github.com/sympy/sympy/pull/13840)
  * add more functions to jscode
    [#13832](https://github.com/sympy/sympy/pull/13832)
  * add support for Max and Min in fcode and octave
    [#13903](https://github.com/sympy/sympy/pull/13903)
  * fix `pycode()` and 'lambdify' for `Piecewise` functions
    [#13969](https://github.com/sympy/sympy/pull/13969)
  * fix imaginary number printing in octave
    [#13978](https://github.com/sympy/sympy/pull/13978)
  * add re, im, arg functions to octave codegen
    [#14013](https://github.com/sympy/sympy/pull/14013)
  * Fix printing of Fortran code with variables that are the same when
    compared case insensitively
    [#14003](https://github.com/sympy/sympy/pull/14003)
  * Add support for sympy.sign in .printing.pycode
    [#14010](https://github.com/sympy/sympy/pull/14010)
  * support zoo and -oo in lambdify
    [#14306](https://github.com/sympy/sympy/pull/14306)
  * lambdify: Improved speed of generated code when unpacking arguments
    [#14691](https://github.com/sympy/sympy/pull/14691)
  * lambdify now generates actual Python functions rather than lambdas
    [#14713](https://github.com/sympy/sympy/pull/14713)
  * the `dummify` argument to `lambdify` now by default only converts the
    arguments to Dummy when necessary
    [#14713](https://github.com/sympy/sympy/pull/14713)
  * Add lambdified function source to the linecache. This makes
    `inspect.getsource`, IPython's `??`, IPython tracebacks, and most
    debuggers show the source code for lambdified functions
    [#14739](https://github.com/sympy/sympy/pull/14739)

* crypto
  * Add Goldwasser Micali Encryption
    [#13666](https://github.com/sympy/sympy/pull/13666)

* discrete
  * new submodule `sympy.discrete` for operating on discrete sequences with
    the following functions:
    * `fft`, `ifft` (fast discrete Fourier transforms), `ntt`, `intt` (number theoretic
      transform) [#14725](https://github.com/sympy/sympy/pull/14725)
    * `convolution` (convolutions on discrete sequences)
      [#14745](https://github.com/sympy/sympy/pull/14745), [#14783](https://github.com/sympy/sympy/pull/14783)
    * `fwht` and `ifwht` (fast Walsh-Hadamard transform)
      [#14765](https://github.com/sympy/sympy/pull/14765)
    * Added the ability to evaluate linear recurrences without obtaining
      closed form expressions
      [#14816](https://github.com/sympy/sympy/pull/14816)

* functions
  * Improve trigonometric function evaluation and logarithmic rewrite
    [#13109](https://github.com/sympy/sympy/pull/13109)
  * `euler` can now compute Euler polynomials
    [#13228](https://github.com/sympy/sympy/pull/13228)
  * add some rewrite methods for `sinc`
    [#11870](https://github.com/sympy/sympy/pull/11870)
  * use gmpy to compute `binomial` if it is installed
    [#13394](https://github.com/sympy/sympy/pull/13394)
  * fix for B-Splines of higher than 1 degree with repeated knots
    [#12214](https://github.com/sympy/sympy/pull/12214)
  * allow Min and Max to be rewritten in terms of Abs
    [#13614](https://github.com/sympy/sympy/pull/13614)
  * add some assumptions for Catalan numbers
    [#13628](https://github.com/sympy/sympy/pull/13628)
  * Added an interpolating_spline function for symbolic interpolation of
    splines [#13829](https://github.com/sympy/sympy/pull/13829)
  * Implement more special values of polylogarithm, without exp_polar for s=1
    [#13852](https://github.com/sympy/sympy/pull/13852)
  * Improved legendre polynomial for negative n
    [#13920](https://github.com/sympy/sympy/pull/13920)
  * Add evaluation of polygamma(0, z) for all rational z
    [#14045](https://github.com/sympy/sympy/pull/14045)
  * More general unpolarification for polylog argument
    [#14076](https://github.com/sympy/sympy/pull/14076)
  * fix `floor` sometimes giving the wrong answer
    [#14167](https://github.com/sympy/sympy/pull/14167)
  * return zeta(2*n) and zeta(-n) as expressions
    [#14178](https://github.com/sympy/sympy/pull/14178)
  * automatic log expansion of numbers removed
    [#14134](https://github.com/sympy/sympy/pull/14134)
  * improve absolute value of complex numbers raised to the power of complex
    numbers [#14278](https://github.com/sympy/sympy/pull/14278)
  * improve evaluation of inverse trig functions
    [#14321](https://github.com/sympy/sympy/pull/14321)
  * allow exp to be rewritten as sqrt
    [#14358](https://github.com/sympy/sympy/pull/14358)
  * evaluate transcendental functions at complex infinity
    [#14406](https://github.com/sympy/sympy/pull/14406)
  * improve automatic evaluation of reciprocal trig functions
    [#14544](https://github.com/sympy/sympy/pull/14544)
  * Support added for computing binomial(n, k) where k can be noninteger and n
    can be any number. [#14019](https://github.com/sympy/sympy/pull/14019) by
    [Yathartha Joshi](https://github.com/Yathartha22)
  * Fix binomial(n, k) for negative integer k
    [#14575](https://github.com/sympy/sympy/pull/14575)
  * Optimize binomial evaluation for integers
    [#14576](https://github.com/sympy/sympy/pull/14576)
  * implemented partition numbers (`partition()`)
    [#14617](https://github.com/sympy/sympy/pull/14617)
  * automatically reduce nested floor and ceiling expressions
    [#14631](https://github.com/sympy/sympy/pull/14631)
  * improve performance Mod of factorial and binomial expressions
    [#14636](https://github.com/sympy/sympy/pull/14636)
  * improve floor and ceiling rewriting and equality testing
    [#14647](https://github.com/sympy/sympy/pull/14647)

* geometry:
  * Second moment and product moment of area of a two-dimensional polygon can
    now be computed. [#13939](https://github.com/sympy/sympy/pull/13939) by
    [Keshri Kumar Rushyam](https://github.com/rushyam).
  * Second moment and product moment of area of an ellipse and a circle can
    now be computed. [#14190](https://github.com/sympy/sympy/pull/14190) by
    [Keshri Kumar Rushyam](https://github.com/rushyam).
  * pairwise intersections.
    [#12963](https://github.com/sympy/sympy/pull/12963)
  * Added `closing_angle` which represents the angle of one linear entity
    relative to another. [#13002](https://github.com/sympy/sympy/pull/13002)
  * Added method to compute the exradius of a triangle
    [#13318](https://github.com/sympy/sympy/pull/13318)
  * Implemented a length property for the Curve class.
    [#13328](https://github.com/sympy/sympy/pull/13328)
  * make arbitrary_point of Plane run through all points
    [#13807](https://github.com/sympy/sympy/pull/13807)
  * Remove integral from ellipse circumference calculation
    [#14435](https://github.com/sympy/sympy/pull/14435)

* groups
  * It is now possible to check if a finitely presented group is infinite with
    `_is_infinite` method (this may return `None` in a number of cases where
    the algorithm cannot establish whether a group is infinite). The `order`
    method now returns `S.Infinity` for some infinite groups.
    ([#12705](https://github.com/sympy/sympy/pull/12705))
  * `subgroup` method was added for permutation and finitely presented groups
    to return the subgroup generated by given group elements
    ([#12658](https://github.com/sympy/sympy/pull/12658)). Subgroups of
    finitely presented groups end up having different generators from the
    original group but a special class `FpSubgroup` can be used as a
    substitute if having the same generators is important.
    ([#12827](https://github.com/sympy/sympy/pull/12827))
  * The presentation of a finitely presented group can be simplified with
    `simplify_presentation`
  * Group homomorphisms have been implemented as a `GroupHomomorphism` class
    in `sympy.combinatorics.homomorphisms`. A homomorphism can be created
    using the function `homomorphism` and additionally one can create special
    types of group action homomorphisms for permutation groups with
    `block_homomorphism` and `orbit_homomorphism`.
    ([#12827](https://github.com/sympy/sympy/pull/12827) and
    [#13104](https://github.com/sympy/sympy/pull/13104))
  * Rewriting systems for finitely presented groups are implemented. If a
    confluent rewriting system is found, this allows to reduce elements to
    their normal forms. Otherwise, at least the found reduction rules cab be
    used to equate some group elements that otherwise would be treated as
    different previously. See
    [#12893](https://github.com/sympy/sympy/pull/12893) for more information.
  * Convert between permutation and finite presentation of groups by using
    `presentation` and `strong_presentation` method of permutation groups
    ([#12986](https://github.com/sympy/sympy/pull/12986) and
    [#13698](https://github.com/sympy/sympy/pull/13698)) and
    `_to_perm_group()` for finitely presented groups
    ([#13119](https://github.com/sympy/sympy/pull/13119))
  * Compute Sylow subgroups of permutation groups with `sylow_subgroup`
    method. ([#13104](https://github.com/sympy/sympy/pull/13104))
  * A number of methods and attributes previously only available for
    permutation groups now can be used with finite finitely presented groups.
    These include `derived_series`, `lower_central_series`, `center`,
    `derived_subgroup`, `centralizer`, `normal_closure`, `is_abelian`,
    `is_nilpotent`, `is_solvable` and `elements`.
    ([#13119](https://github.com/sympy/sympy/pull/13119))

* holonomic
  * Generalize Holonomic to work on symbolic powers
    [#12989](https://github.com/sympy/sympy/pull/12989)

* integrals
  * Rewrite Abs and sign as Piecewise for
    integration[#13930](https://github.com/sympy/sympy/pull/13930)
  * Integrate Max and Min by rewriting them as Piecewise
    [#13919](https://github.com/sympy/sympy/pull/13919)
  * Add new trigonometric rule in manual integration
    [#12651](https://github.com/sympy/sympy/pull/12651)
  * Reorder Piecewise output of integration, so that generic answer is first
    [#13998](https://github.com/sympy/sympy/pull/13998)
  * Add symbolic Riemann sums for definite integrals
    [#13988](https://github.com/sympy/sympy/pull/13988)
  * In manualintegrate, when integrating by parts, do not use u = non-poly
    algebraic [#14015](https://github.com/sympy/sympy/pull/14015)
  * fix wrong result integration of rational functions in some cases when
    variables have assumptions
    [#14082](https://github.com/sympy/sympy/pull/14082)
  * simplify some convergence conditions for integrals
    [#14092](https://github.com/sympy/sympy/pull/14092)
  * add a manualintegrate rule for expanding trig functions
    [#14408](https://github.com/sympy/sympy/pull/14408)
  * improve manualintegrate for substitutions `u=(a*x+b)**(1/n)`
    [#14480](https://github.com/sympy/sympy/pull/14480)
  * better handling of manual, meijerg, risch flags in integrate
    [#14475](https://github.com/sympy/sympy/pull/14475)
  * add `floor` to certain discontinuous integrals
    [#13808](https://github.com/sympy/sympy/pull/13808)
  * add integration of orthogonal polynomials of general degree
    [#14521](https://github.com/sympy/sympy/pull/14521)
  * allow integrals with inequalities, such as Integral(x,
    x>2) [#14586](https://github.com/sympy/sympy/pull/14586)

* interpolation
  * A spline of given degree that interpolates given data points can be
    constructed with `interpolating_spline`.
    [#13829](https://github.com/sympy/sympy/pull/13829) by
    [Jashan](https://github.com/jashan498).

* liealgebras
  * fix instantiate of CartanType with a string like CartanType('A34')
  [#14568](https://github.com/sympy/sympy/pull/14568)

* matrices
  * Computing the Smith Normal Form of a matrix over a ring is now implemented
    as the function `smith_normal_form` from `sympy.matrices.normalforms`
    ([#12705](https://github.com/sympy/sympy/pull/12705))
  * Derivatives for expressions of matrix symbols now experimentally
    supported.
  * Matrices can be used as deriving variable.
  * Matrix norm for order 1 has been added
    [#12616](https://github.com/sympy/sympy/pull/12616)
  * add MatrixExpr.from_index_summation, which parses expression of matrices
    with explicitly summed indices into a matrix expression without indices,
    if possible [#13542](https://github.com/sympy/sympy/pull/13542)
  * Add functionality for infinity norm of matrices
    [#13986](https://github.com/sympy/sympy/pull/13986)
  * add numeric check for pivot being zero in Bareiss determinant method
    [#13877](https://github.com/sympy/sympy/pull/13877)
  * Implement Kronecker product of Matrices
    [#14264](https://github.com/sympy/sympy/pull/14264)
  * give a simpler representation of exp(M) when M is real
    [#14331](https://github.com/sympy/sympy/pull/14331)
  * avoid loss of precision in jordan_form
    [#13982](https://github.com/sympy/sympy/pull/13982)
  * made Mod elementwise for matrices
    [#14498](https://github.com/sympy/sympy/pull/14498)
  * implement Cholesky and LDL decompositions for Hermitian matrices
    [#14474](https://github.com/sympy/sympy/pull/14474)

* ntheory
  * Added totient and mobius range methods to Sieve
    [#14628](https://github.com/sympy/sympy/pull/14628)

* physics.continuum_mechanics
  * Added applied_loads and remove_load methods
    [#14751](https://github.com/sympy/sympy/pull/14751)
  * added method to find point of contraflexure
    [#14753](https://github.com/sympy/sympy/pull/14753)
  * Added support for composite beams
    [#14773](https://github.com/sympy/sympy/pull/14773)
  * added `apply_support` and `max_deflection` methods
    [#14786](https://github.com/sympy/sympy/pull/14786)

* physics.mechanics
  * add gravity function [#14171](https://github.com/sympy/sympy/pull/14171)

* physics.optics
  * Added transverse_magnification
    [#10625](https://github.com/sympy/sympy/pull/10625)
  * Implemented Brewster's Angle in Optics Module
    [#13756](https://github.com/sympy/sympy/pull/13756)

* physics.quantum
  * Adding support for simplifying powers of tensorproducts
    [#13974](https://github.com/sympy/sympy/pull/13974)

* physics.vector
  * fix error pretty printing physics vectors
    [#14717](https://github.com/sympy/sympy/pull/14717)

* physics.wigner
  * Make wigner_9j work for certain half-integer argument combinations
    [#13602](https://github.com/sympy/sympy/pull/13602)

* plotting
  * Fix plotting of constant functions
    [#14023](https://github.com/sympy/sympy/pull/14023)

* polys
  * `degree` now requires a generator to be specified for multivariate
    polynomials (use `total_degree` for the total degree).
    [#13173](https://github.com/sympy/sympy/pull/13173)
  * `total_degree` function added
    [#13277](https://github.com/sympy/sympy/pull/13277)
  * Allow `itermonomials` to respect non-commutative variables
    [#13327](https://github.com/sympy/sympy/pull/13327)
  * Improve srepr of polynomial rings and fraction fields
    [#13345](https://github.com/sympy/sympy/pull/13345)
  * add `Poly.norm`, which computes the conjugates of a polynomial over a
    number field. [#13304](https://github.com/sympy/sympy/pull/13304)
  * add `srepr` printer for `DMP`
    [#13367](https://github.com/sympy/sympy/pull/13367)
  * added Finite ring extensions to the `agca` submodule
    [#13378](https://github.com/sympy/sympy/pull/13378)
  * fix factor for expressions with floating point coefficients
    [#13198](https://github.com/sympy/sympy/pull/13198)
  * Changed ModularInteger to use fast exponentiation
    [#14093](https://github.com/sympy/sympy/pull/14093)
  * fix minpoly(I) over domains that contain I
    [#14382](https://github.com/sympy/sympy/pull/14382)
  * fix the quartic root solver for certain quartic polynomials with complex
    coefficients [#14522](https://github.com/sympy/sympy/pull/14522)
  * implement Dixons and Macaulay multivariate resultants
    [#14370](https://github.com/sympy/sympy/pull/14370)
  * support gcd and lcm for compatible irrational numbers
    [#14365](https://github.com/sympy/sympy/pull/14365)
  * optimized Lagrange Interpolation
    [#14603](https://github.com/sympy/sympy/pull/14603)

* printing
  * Latex printer now supports custom printing of logarithmic functions by
    newly by accepting `ln_notation` as a boolean (default=`False`) keyword
    argument. ([#14180](https://github.com/sympy/sympy/pull/14180))
  * Add `mathml` and `cxxcode` to `from sympy import *`.
    [#12937](https://github.com/sympy/sympy/pull/12937)
  * Add `sympy_integers` option to the str printer to print Rationals in a
    SymPy recreatable way. [#13141](https://github.com/sympy/sympy/pull/13141)
  * change the set pretty printer to print with {}
    [#12087](https://github.com/sympy/sympy/pull/12087)
  * fix LaTeX dagger printing
    [#13672](https://github.com/sympy/sympy/pull/13672)
  * use a better symbol for Equivalent in the pretty printers
    [#14105](https://github.com/sympy/sympy/pull/14105)
  * fix pretty printing of DiracDelta
    [#14104](https://github.com/sympy/sympy/pull/14104)
  * change LaTeX printing of O() from `\mathcal{O}` to `\big{O}`
    [#14166](https://github.com/sympy/sympy/pull/14166)
  * print Poly terms in the correct order in the latex printer
    [#14317](https://github.com/sympy/sympy/pull/14317)
  * fix latex printing of SeqFormula
    [#13971](https://github.com/sympy/sympy/pull/13971)
  * add abbreviated printing for units
    [#13962](https://github.com/sympy/sympy/pull/13962)
  * allow user defined mul_symbol in latex()
    [#13798](https://github.com/sympy/sympy/pull/13798)
  * add a presentation MathML printer
    [#13794](https://github.com/sympy/sympy/pull/13794)
  * fix an issue with some missing parentheses from pprint and latex
    [#13673](https://github.com/sympy/sympy/pull/13673)
  * fix some instances where the str printer would not reuse the same printer
    class [#14531](https://github.com/sympy/sympy/pull/14531)
  * improve printing of expressions like `Pow(Mul(a,a,evaluate=False), -1,
    evaluate=False)` [#14207](https://github.com/sympy/sympy/pull/14207)
  * add conjugate to Mathematica printing
    [#14109](https://github.com/sympy/sympy/pull/14109)
  * the printers no longer dispatch undefined functions like `Function`
    subclasses (makes `Function('gamma')` print as `γ` instead of `Γ`)
    [#13822](https://github.com/sympy/sympy/pull/13822)
  * Make LaTeX printer print full trig names for acsc and asec
    [#14774](https://github.com/sympy/sympy/pull/14774)

* series:
  * Bidirectional limits can now be computed by passing dir=+- argument to
    `limits.limit` function.
    [#11694](https://github.com/sympy/sympy/issue/11694) by [Gaurav
    Dhingra](https://github.com/gxyd).
  * Evaluate limits of sequences with alternating signs
    [#13976](https://github.com/sympy/sympy/pull/13976)

* sets:
  * Ordinals can now be represented in Cantor normal form, and arithmetics can
    be performed which includes addition, multiplication, and basic
    exponentiation. [#13682](https://github.com/sympy/sympy/pull/13682) by
    [Ashish Kumar Gaurav](https://github.com/ashishkg0022)
  * SetExpr and arithmetic expressions of sets now supported (via
    multimethods). [#14106](https://github.com/sympy/sympy/pull/14106)
  * Singleton sets (Reals, Complexes, etc.) can now be accessed without `S`
    [#11383](https://github.com/sympy/sympy/pull/11383),
    [#12524](https://github.com/sympy/sympy/pull/12524),
    [#13572](https://github.com/sympy/sympy/pull/13572),
    [#14844](https://github.com/sympy/sympy/pull/14844)
  * Add set expressions [#2721](https://github.com/sympy/sympy/pull/2721),
    [#14301](https://github.com/sympy/sympy/pull/14301)
  * ImageSet now supports multiple sets
    [#14145](https://github.com/sympy/sympy/pull/14145)
  * be more careful in ConditionSet.subs
    [#14564](https://github.com/sympy/sympy/pull/14564)

* simplify
  * improve simplification of Min and Max
    [#13054](https://github.com/sympy/sympy/pull/13054),
    [#13599](https://github.com/sympy/sympy/pull/13599)
  * New function `gammasimp` separated from `combsimp`. `combsimp` does not
    apply gamma function simplifications that may make an integer argument
    non-integer. Also various improvements to both.
    [#13210](https://github.com/sympy/sympy/pull/13210)
  * remove unused fu flag from `simplify`.
    [#13264](https://github.com/sympy/sympy/pull/13264)
  * add `rational` flag to `simplify`.
    [#13264](https://github.com/sympy/sympy/pull/13264)
  * improved simplification of hyperbolic functions
    [#13259](https://github.com/sympy/sympy/pull/13259)
  * improve the efficiency of `cse`
    [#13221](https://github.com/sympy/sympy/pull/13221)
  * Allow cse of unevaluated expressions
    [#13271](https://github.com/sympy/sympy/pull/13271)
  * fix logcombine for logs of numbers
    [#14070](https://github.com/sympy/sympy/pull/14070)
  * disable simplification of inverses in simplify() unless the new `inverse`
    flag is set [#14422](https://github.com/sympy/sympy/pull/14422)
  * `simplify()` now simplifies non-commutative expressions
    [#14520](https://github.com/sympy/sympy/pull/14520)

* solvers
  * Enable initial condition solving in `dsolve`
    [#11264](https://github.com/sympy/sympy/pull/11264)
  * Added support for solving inequalities involving rational functions with
    imaginary coefficients [#13296](https://github.com/sympy/sympy/pull/13296)
  * the solvers now work with non-Symbols such as Indexed
    [#13415](https://github.com/sympy/sympy/pull/13415)
  * add failing_assumptions function
    [#12147](https://github.com/sympy/sympy/pull/12147)
  * Improve the solver for linear 1st order ODE systems of size 2
    [#13812](https://github.com/sympy/sympy/pull/13812)
  * fix classify_ode(dict=True) for Eq
    [#14663](https://github.com/sympy/sympy/pull/14663)
  * improve handling of infinite solutions in `solve`
    [#14749](https://github.com/sympy/sympy/pull/14749)

* solveset
  * Solveset now supports exponential equations with negative base.
    [#13923](https://github.com/sympy/sympy/pull/13923) by [Yathartha
    Joshi](https://github.com/Yathartha22)
  * Fix `solve_univariate_inequality` for finite set domains
    [#13458](https://github.com/sympy/sympy/pull/13458)
  * solve more trig equations
    [#13941](https://github.com/sympy/sympy/pull/13941)
  * improve solveset with piecewise expressions
    [#14253](https://github.com/sympy/sympy/pull/14253)
  * Improved solveset for negative base exponential equations
    [#13844](https://github.com/sympy/sympy/pull/13844)
  * allow solving equations with Abs in solveset
    [#14449](https://github.com/sympy/sympy/pull/14449)

* stats
  * Added pre-computed cumulative distribution functions to some Random
    Symbols [#13284](https://github.com/sympy/sympy/pull/13284),
    [#13804](https://github.com/sympy/sympy/pull/13804),
    [#13878](https://github.com/sympy/sympy/pull/13878)
  * add trapezoidal distribution
    [#13419](https://github.com/sympy/sympy/pull/13419)
  * The characteristic function of a probability distribution can be computed
    with `characteristic_function`.
    [#13851](https://github.com/sympy/sympy/pull/13851) and
    [#13958](https://github.com/sympy/sympy/pull/13958) by [Ethan
    Ward](https://github.com/ethankward).
  * Probability of continuous random variables lying in a finite set is now
    zero [#14254](https://github.com/sympy/sympy/pull/14254)
  * add sampling for GammaInverse distribution
    [#14250](https://github.com/sympy/sympy/pull/14250)
  * Allow Geometric RVs where `p` is a symbol
    [#14472](https://github.com/sympy/sympy/pull/14472)
  * various improvements to sampling methods
  * fix wrong results with Or conditions
    [#14578](https://github.com/sympy/sympy/pull/14578)
  * implemented probability for discrete random variables
    [#14119](https://github.com/sympy/sympy/pull/14119)
  * rename `restricted_domain` to `where` for discrete random variables
    [#14604](https://github.com/sympy/sympy/pull/14604)
  * implement several missing classes in discrete random variables
    [#14218](https://github.com/sympy/sympy/pull/14218)

* tensor
  * do not require assumptions to be set on Idx bounds.
    [#12888](https://github.com/sympy/sympy/pull/12888)
  * improve `Indexed.free_symbols`
    [#13360](https://github.com/sympy/sympy/pull/13360)

* units
  * add SI base units to sympy.physics.units.systems
    [#12897](https://github.com/sympy/sympy/pull/12897)
  * Implemented get_dimensional_expr for Derivative
    [#13003](https://github.com/sympy/sympy/pull/13003)
  * Implemented Quantity.get_dimensional_expr() for functions
    [#13011](https://github.com/sympy/sympy/pull/13011)
  * the relation between base dimensions and derived dimensions are now part
    of DimensionSystem, so that they are no longer absolute.
    [#13287](https://github.com/sympy/sympy/pull/13287)
  * Add Stefan Boltzmann constant
    [#13440](https://github.com/sympy/sympy/pull/13440)
  * Add Planck charge and derived Planck units
    [#13438](https://github.com/sympy/sympy/pull/13438)
  * Add katal, gray to derived units
    [#13658](https://github.com/sympy/sympy/pull/13658)
  * Added derived unit of Radioactivity
    [#13839](https://github.com/sympy/sympy/pull/13839)
  * fix subs for Quantities [#13855](https://github.com/sympy/sympy/pull/13855)
  * add simplification of quantities
    [#14286](https://github.com/sympy/sympy/pull/14286)

* vector
  * fix vector + 0 [#14711](https://github.com/sympy/sympy/pull/14711)

## Minor changes

* `free_symbols` and `find_dynamicsymbols` methods now available for vectors
  directly, if accompanied by a reference frame argument.
  [#13549](https://github.com/sympy/sympy/pull/13549) by [Saloni
  Jain](https://github.com/tosalonijain)

* simplify `Relational.canonical`
  [#12906](https://github.com/sympy/sympy/pull/12906)

* fix `(z**r).is_algebraic` where `z` is algebraic and `r` is rational
  [#12924](https://github.com/sympy/sympy/pull/12924)[<8;52;35m

* Remove `register` keyword from C++17 standard in `cxxcode`
  [#12964](https://github.com/sympy/sympy/pull/12964)

* Allow `autowrap`'s tempdir to be a relative path
  [#12944](https://github.com/sympy/sympy/pull/12944)

* Fix symbols with superscripts raised to a power in the LaTeX printer
  [#12894](https://github.com/sympy/sympy/pull/12894)

* Fix conversion of undefined functions (like `Function('f')`) to Sage.
  [#12826](https://github.com/sympy/sympy/pull/12826)

* Fix wrong result integrating derivatives of multiple variables
  [#12971](https://github.com/sympy/sympy/pull/12971)

* Rich comparison methods now return `NotImplemented` when comparing against
  unknown types [#13091](https://github.com/sympy/sympy/pull/13091)

* Add/Fix logarithmic rewrites of inverse hyperbolic functions
  [#13099](https://github.com/sympy/sympy/pull/13099)

* Fix Mul.expand(deep=False)
  [#13281](https://github.com/sympy/sympy/pull/13281)

* Make DiracDelta(-x) == DiracDelta(x)
  [#13308](https://github.com/sympy/sympy/pull/13308)

* `linsolve` now raises error for non-linear equations
  [#13325](https://github.com/sympy/sympy/pull/13325)

* vlatex: added brackets in multiplication
  [#12299](https://github.com/sympy/sympy/pull/12299)

* Add "The Zen of SymPy" (`import sympy.this`)

* Install isympy using setuptools, making it available on Windows. isympy can
  also now be run as `python -m isympy`
  [#13193](https://github.com/sympy/sympy/pull/13193)

* improve evaluation performance of `binomial`
  [#13484](https://github.com/sympy/sympy/pull/13484)

* Add support for more than two operands in numpy logical and/or
  representations in lambdify
  [#12608](https://github.com/sympy/sympy/pull/12608)

* The Mathematica parsing function has been rewritten
  [#13533](https://github.com/sympy/sympy/pull/13533)

* The Mathematica parsing function now has an `additional_translations` flag
  [#13544](https://github.com/sympy/sympy/pull/13544)

* Fix is_real for trigonometric and hyperbolic functions
  [#13678](https://github.com/sympy/sympy/pull/13678)

* @/__matmul__ now only performs matrix multiplication
  [#13773](https://github.com/sympy/sympy/pull/13773)

* Fold expressions with Piecewise before trying to integrate them
  [#13866](https://github.com/sympy/sympy/pull/13866)

* Fix `has` for non-commutative Muls in some cases
  [#14026](https://github.com/sympy/sympy/pull/14026)

* Avoid recursive calls for upper and lower gamma
  [#14021](https://github.com/sympy/sympy/pull/14021)

* Remove the sympy_tokenize module in favor of the standard library tokenize.
  Fixes sympification of Python 3-only idioms, like `sympify('α')`.
  [#14085](https://github.com/sympy/sympy/pull/14085)

* Check for logarithmic singularities in `_eval_interval`
  [#14097](https://github.com/sympy/sympy/pull/14097)

* Simple optimization to speed up LCM
  [#14314](https://github.com/sympy/sympy/pull/14314)

* Use extended Euclidean algorithm instead of totient calculation
  for modular matrix inverse
  [#14347](https://github.com/sympy/sympy/pull/14347)

## Authors

The following people contributed at least one patch to this release (names are
given in alphabetical order by last name). A total of 170 people
contributed to this release. People with a * by their names contributed a
patch for the first time for this release; 124 people contributed
for the first time for this release.

Thanks to everyone who contributed to this release!

- Saurabh Agarwal*
- Arif Ahmed
- Jonathan Allan*
- anca-mc*
- Adwait Baokar*
- Nilabja Bhattacharya*
- Johan Blåbäck
- Nicholas Bollweg*
- Francesco Bonazzi
- Matthew Brett
- Marcin Briański
- Bulat*
- Ondřej Čertík
- Arighna Chakrabarty*
- Rishav Chakraborty*
- Ravi charan*
- Lev Chelyadinov*
- Poom Chiarawongse*
- James Cotton*
- cym1*
- czgdp1807*
- Björn Dahlgren
- David Daly*
- der-blaue-elefant*
- Gaurav Dhingra
- dps7ud*
- Rob Drynkin*
- Seth Ebner*
- Peter Enenkel*
- Fredrik Eriksson*
- Boris Ettinger*
- eward*
- Isuru Fernando
- Segev Finer*
- Caley Finn*
- Micah Fitch*
- Lucas Gallindo*
- Bradley Gannon*
- Mauro Garavello
- Varun Garg
- Ashish Kumar Gaurav*
- Jithin D. George*
- Sourav Ghosh*
- Valeriia Gladkova
- Jeremey Gluck*
- Nikoleta Glynatsi*
- Keno Goertz*
- Nityananda Gohain*
- Filip Gokstorp*
- Sayan Goswami*
- Jonathan A. Gross*
- Theodore Han
- Rupesh Harode*
- James Harrop*
- Rahil Hastu*
- helo9*
- Himanshu*
- Hugo*
- David Menéndez Hurtado*
- Ayodeji Ige*
- Itay4*
- Harsh Jain
- Samyak Jain
- Saloni Jain*
- Rohit Jain*
- Shikhar Jaiswal
- Mark Jeromin*
- JMSS-Unknown*
- Yathartha Joshi
- Ishan Joshi*
- Salil Vishnu Kapur*
- Atharva Khare*
- Abhigyan Khaund*
- Sergey B Kirpichev
- Leonid Kovalev
- Amit Kumar
- Jiri Kuncar
- Akash Kundu*
- Himanshu Ladia*
- Rémy Léone*
- Alex Lubbock*
- Jared Lumpe*
- luz.paz*
- Colin B. Macdonald
- Shubham Maheshwari*
- Akshat Maheshwari*
- Shikhar Makhija
- Amit Manchanda*
- Marco Mancini*
- Cezary Marczak*
- Yuki Matsuda*
- Bhautik Mavani
- Maxence Mayrand*
- B McG*
- Cavendish McKay*
- Ehren Metcalfe*
- Aaron Meurer
- Peleg Michaeli
- Szymon Mieszczak
- Aaron Miller*
- Joaquim Monserrat*
- Jason Moore
- Sidhant Nagpal*
- Abdullah Javed Nesar
- Javed Nissar*
- Richard Otis
- Austin Palmer*
- Nikhil Pappu*
- Fermi Paradox
- Rhea Parekh*
- Arihant Parsoya
- Roberto Díaz Pérez*
- Cristian Di Pietrantonio*
- Waldir Pimenta*
- Robert Pollak*
- Alexander Pozdneev*
- P. Sai Prasanth*
- Rastislav Rabatin*
- Zach Raines*
- Shekhar Prasad Rajak
- Juha Remes
- Matthew Rocklin
- Phil Ruffwind
- rushyam*
- Saketh*
- Carl Sandrock*
- Kshitij Saraogi
- Nirmal Sarswat*
- Subhash Saurabh*
- Dmitry Savransky*
- Nico Schlömer
- Stan Schymanski*
- sfoo*
- Ayush Shridhar*
- shruti
- Sartaj Singh
- Rajeev Singh*
- Mayank Singh*
- Arshdeep Singh*
- Jashanpreet Singh*
- Malkhan Singh*
- Gleb Siroki*
- Chris Smith
- Ralf Stephan
- Kalevi Suominen
- Ian Swire*
- symbolique*
- Mihail Tarigradschi*
- James Taylor*
- Pavel Tkachenko*
- Cédric Travelletti*
- Tschijnmo TSCHAU
- Wes Turner*
- Unknown*
- Akash Vaish*
- vedantc98*
- Pauli Virtanen
- Vishal*
- Stewart Wadsworth*
- Ken Wakita*
- Ethan Ward*
- Matthew Wardrop*
- Daniel Wennberg*
- Lucas Wiman*
- Kiyohito Yamazaki*
- Yang Yang*
- Ka Yi
- ylemkimon*
- zhouzq-thu*
- Rob Zinkov*
