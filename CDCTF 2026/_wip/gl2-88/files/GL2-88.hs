#! /usr/bin/env runghc
{-# LANGUAGE LambdaCase #-}
 
import Data.Word (Word8)
import Data.List (nub, transpose)
import Data.Char (ord, chr)
import System.Environment (getArgs)


-- Alphabet Size
_P :: Int
_P = 67 

-- Key Length 
_Q :: Int
_Q = 11

-- Note P = 1 mod Q

-- Define the space of integers mod P
newtype Z67 = Z67 Int deriving (Eq, Ord, Enum)

instance Num Z67 where 
    (Z67 a) + (Z67 b) = Z67 $ (a + b) `mod` _P
    (Z67 a) * (Z67 b) = Z67 $ (a * b) `mod` _P
    negate (Z67 a) = Z67 $ (_P - a)  `mod` _P
    abs = id 
    signum (Z67 a) = Z67 $ signum a
    fromInteger a = Z67 $ fromInteger a `mod` _P

instance Show Z67 where
    show (Z67 a) = show a ++ " (mod 67)"


-- Operating on the field of Z67, define vectors and matrices 
type Scalar = Z67
type Vector = (Scalar, Scalar)
type Matrix = (Vector, Vector)

field :: [Scalar]
field = [0..66]

-- Identity matrix
e :: Matrix 
e = ((1,0),(0,1))

-- Matrix transpose
t :: Matrix -> Matrix
t ((a, b),(c,d)) = ((a,c),(b,d))

-- Dot product
(*.) :: Vector -> Vector -> Scalar
(a1, b1) *. (a2, b2) = a1*a2 + b1*b2

-- Matrix-vector multiplication
(*/) :: Matrix -> Vector -> Vector 
(r1, r2) */ v = (r1 *. v, r2 *. v)

-- Matrix-matrix multiplication
(*.*) :: Matrix -> Matrix -> Matrix 
(r1, r2) *.* m2 = 
    let (c1, c2) = t m2 
     in ((r1 *. c1, r1 *. c2), (r2 *. c1, r2 *. c2))

-- Matrix power 
(*^*) :: Matrix -> Scalar -> Matrix
m *^* n = foldr (\_ acc -> m *.* acc) e [1..n]

-- Determinant
det :: Matrix -> Scalar
det ((a, b), (c, d)) = a*d - c*d

-- Multiplicative inverse: given v, find x s.t. v*x = 1 mod P
inv :: Scalar -> Scalar
inv (Z67 v) = Z67 . (`mod` _P) . snd $ go _P v
    where         
        go :: Int -> Int -> (Int, Int)
        go n = \case
            1 -> (0, 1)
            x -> let (tq, tr) = n `quotRem` x 
                     (nq, nr) = go x tr  
                 in  (nr, nq - nr*tq)

-- Inverse of a 2x2 matrix
minv :: Matrix -> Matrix 
minv m@((a, b),(c, d)) = 
    let f = inv $ det m
    in  ((f*d, -(f*b)), (-(f*c), f*a))

-- Matrix A with order P
_A :: Matrix
_A = ((1, 1), (0, 1))

-- Matrix B with order Q
_B :: Matrix
_B = ((9, 0), (0, 1))

-- Note that A and B commute A non-abelian subgroup of GL2(Zp) containing P*Q elements
grp :: [Matrix]
grp = [(_A *^* a) *.* (_B *^* b) | a <- [0..Z67 (_P-1)], b <- [0..Z67 (_Q-1)]]

-- Left cosets of md in gp
(//) :: [Matrix] -> [Matrix] -> [[Matrix]]
gp // md = (\m -> (*.* m) <$> gp) <$> md 

-- Map a character between '<' and '~' to an element of Zp
c2s :: Char -> Scalar 
c2s c = Z67 $ ord c - ord '<'

-- Map an element of Zp to a character between '<' and '~'
s2c :: Scalar -> Char
s2c (Z67 s) = chr (s + ord '<') 

-- Generate a keystream based on iterations of grp mod key 
-- Collapse by Q matrices (key length)
getKeyStream :: String -> [Matrix]
getKeyStream key = foldr (const round) l [0.._Q]
    where
        m0 :: [Matrix] 
        m0 = [((1, c2s x), (0, 1)) | x <- key]

        go :: [Matrix] -> [Matrix]
        go = concat . tail . transpose . (grp //)
    
        l :: [Matrix]
        l = concat $ iterate go m0

        round :: [Matrix] -> [Matrix]
        round tl = zipWith (*.*) tl (tail tl)

string2Vecs :: String -> [Vector]
string2Vecs = map (\c -> (c2s c, -1))

vecs2String :: [Vector] -> String
vecs2String = map (s2c . fst)

encrypt :: String -> String -> String 
encrypt key plaintext = vecs2String $ zipWith (*/) (getKeyStream key) (string2Vecs plaintext)

decrypt :: String -> String -> String 
decrypt key plaintext = vecs2String $ zipWith (\x y -> minv x */ y) (getKeyStream key) (string2Vecs plaintext)

main :: IO()
main = do 
    args <- getArgs
    case args of 
      ["encrypt", key, message]
        | length key /= 11 -> putStrLn "Key should be of length 11" 
        | otherwise        -> putStrLn $ encrypt key message 
      ["decrypt", key, message]
                           -> putStrLn $ decrypt key message 
      _                    -> putStrLn "Usage: ./GL2-88.hs <encrypt/decrypt> <key> <message>"
