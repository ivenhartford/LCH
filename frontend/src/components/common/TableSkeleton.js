import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Skeleton,
  Paper,
} from '@mui/material';

/**
 * TableSkeleton Component
 *
 * Displays a loading skeleton for table data while content is being fetched.
 * Provides better perceived performance than a simple spinner.
 *
 * Props:
 * - rows: Number - Number of skeleton rows to display (default: 5)
 * - columns: Number - Number of columns in the table (default: 6)
 * - headers: Array<string> - Optional array of header labels
 * - showHeaders: Boolean - Whether to show table headers (default: true)
 *
 * Usage:
 * ```jsx
 * if (isLoading) {
 *   return (
 *     <TableSkeleton
 *       rows={10}
 *       columns={6}
 *       headers={['Name', 'Email', 'Phone', 'City', 'Status', 'Balance']}
 *     />
 *   );
 * }
 * ```
 */
const TableSkeleton = ({ rows = 5, columns = 6, headers = [], showHeaders = true }) => {
  return (
    <TableContainer component={Paper}>
      <Table>
        {showHeaders && (
          <TableHead>
            <TableRow>
              {headers.length > 0
                ? headers.map((header, index) => (
                    <TableCell key={index}>
                      <Skeleton variant="text" width="80%" />
                    </TableCell>
                  ))
                : Array.from({ length: columns }).map((_, index) => (
                    <TableCell key={index}>
                      <Skeleton variant="text" width="80%" />
                    </TableCell>
                  ))}
            </TableRow>
          </TableHead>
        )}
        <TableBody>
          {Array.from({ length: rows }).map((_, rowIndex) => (
            <TableRow key={rowIndex}>
              {Array.from({ length: columns }).map((_, colIndex) => (
                <TableCell key={colIndex}>
                  <Skeleton variant="text" width={colIndex === 0 ? '60%' : '90%'} />
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default TableSkeleton;
