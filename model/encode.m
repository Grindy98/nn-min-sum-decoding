function codeword = encode(parityCheckMatrix, message)
% ENCODE   Encode a given codeword, given a parity check matrix
%   parityCheckMatrix should be in systematic form
%   Returns the encoded message

% Find the generator matrix, given the parityCheckMatrix 
genmat = gen2par(parityCheckMatrix);

n_pcm = size(parityCheckMatrix, 1); % number of rows of parityCheckMatrix
m_pcm = size(parityCheckMatrix, 2); % number of cols of parityCheckMatrix

if size(message, 2) ~=  (m_pcm - n_pcm)
    error(['The message length and the dimensions for the parity check' ...
        ' matrix don''t match']);
end

codeword = mod(message * genmat, 2);

end