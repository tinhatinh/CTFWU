use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    program::{invoke, invoke_signed},
    program_error::ProgramError,
    pubkey::Pubkey,
};

pub const DECIMALS: u8 = 6;
pub const AUTH_SEED: &[u8] = b"authority";
pub const SWAP_FEE_BPS: u64 = 100;

#[derive(BorshSerialize, BorshDeserialize, Debug)]
pub struct Pool {
    pub initialized: bool,
    pub bump: u8,
    pub vault_a: Pubkey,
    pub vault_b: Pubkey,
    pub mint_a: Pubkey,
    pub mint_b: Pubkey,
}

#[derive(BorshSerialize, BorshDeserialize, Debug)]
pub enum Ix {
    InitPool,
    SwapAToB { amount: u64 },
    SwapBToA { amount: u64 },
}

fn read_pool(ai: &AccountInfo, program_id: &Pubkey) -> Result<Pool, ProgramError> {
    if ai.owner != program_id {
        return Err(ProgramError::IllegalOwner);
    }
    let data = ai.data.borrow();
    let mut slice: &[u8] = &data[..];
    Pool::deserialize(&mut slice).map_err(|_| ProgramError::InvalidAccountData)
}

pub fn process(program_id: &Pubkey, accounts: &[AccountInfo], input: &[u8]) -> ProgramResult {
    let ix = Ix::try_from_slice(input).map_err(|_| ProgramError::InvalidInstructionData)?;
    let it = &mut accounts.iter();
    match ix {
        Ix::InitPool => {
            let pool = next_account_info(it)?;
            let vault_a = next_account_info(it)?;
            let vault_b = next_account_info(it)?;
            let mint_a = next_account_info(it)?;
            let mint_b = next_account_info(it)?;
            if read_pool(pool, program_id)?.initialized {
                return Err(ProgramError::AccountAlreadyInitialized);
            }
            let (_, bump) = Pubkey::find_program_address(&[AUTH_SEED], program_id);
            let p = Pool {
                initialized: true,
                bump,
                vault_a: *vault_a.key,
                vault_b: *vault_b.key,
                mint_a: *mint_a.key,
                mint_b: *mint_b.key,
            };
            let mut buf = Vec::new();
            p.serialize(&mut buf).map_err(|_| ProgramError::InvalidAccountData)?;
            let mut data = pool.data.borrow_mut();
            if buf.len() > data.len() {
                return Err(ProgramError::AccountDataTooSmall);
            }
            data[..buf.len()].copy_from_slice(&buf);
        }
        Ix::SwapAToB { amount } => swap(program_id, it, amount, true)?,
        Ix::SwapBToA { amount } => swap(program_id, it, amount, false)?,
    }
    Ok(())
}

fn swap<'a, 'b>(
    program_id: &Pubkey,
    it: &mut std::slice::Iter<'a, AccountInfo<'b>>,
    amount: u64,
    a_to_b: bool,
) -> ProgramResult {
    let pool = next_account_info(it)?;
    let authority = next_account_info(it)?;
    let user = next_account_info(it)?;
    let user_src = next_account_info(it)?;
    let user_dst = next_account_info(it)?;
    let vault_src = next_account_info(it)?;
    let vault_dst = next_account_info(it)?;
    let mint_src = next_account_info(it)?;
    let mint_dst = next_account_info(it)?;
    let token_program = next_account_info(it)?;

    let p = read_pool(pool, program_id)?;
    if !p.initialized {
        return Err(ProgramError::UninitializedAccount);
    }
    if !user.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }
    let (auth_pda, _) = Pubkey::find_program_address(&[AUTH_SEED], program_id);
    if *authority.key != auth_pda {
        return Err(ProgramError::InvalidArgument);
    }
    let (want_src, want_dst) = if a_to_b { (p.vault_a, p.vault_b) } else { (p.vault_b, p.vault_a) };
    if *vault_src.key != want_src || *vault_dst.key != want_dst {
        return Err(ProgramError::InvalidArgument);
    }

    let in_ix = spl_token_2022::instruction::transfer_checked(
        token_program.key, user_src.key, mint_src.key, vault_src.key, user.key, &[], amount, DECIMALS,
    )?;
    invoke(&in_ix, &[user_src.clone(), mint_src.clone(), vault_src.clone(), user.clone(), token_program.clone()])?;

    let payout = amount - amount * SWAP_FEE_BPS / 10_000;
    let out_ix = spl_token_2022::instruction::transfer_checked(
        token_program.key, vault_dst.key, mint_dst.key, user_dst.key, authority.key, &[], payout, DECIMALS,
    )?;
    invoke_signed(
        &out_ix,
        &[vault_dst.clone(), mint_dst.clone(), user_dst.clone(), authority.clone(), token_program.clone()],
        &[&[AUTH_SEED, &[p.bump]]],
    )?;

    Ok(())
}

#[cfg(not(feature = "no-entrypoint"))]
solana_program::entrypoint!(entry);
#[cfg(not(feature = "no-entrypoint"))]
pub fn entry(program_id: &Pubkey, accounts: &[AccountInfo], input: &[u8]) -> ProgramResult {
    process(program_id, accounts, input)
}
